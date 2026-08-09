import subprocess
import unittest
from pathlib import Path

import yaml


CHART = Path(__file__).resolve().parents[1]
PINNED_IMAGE = (
    "ghcr.io/coreydaley/messagepit"
    "@sha256:04bd1a2f82c8b90aec52c6bfa4090ef1088acb025f5193f75112207886ef0a02"
)


def helm_template(values_file=None, *extra_args):
    command = ["helm", "template", "test", str(CHART)]
    if values_file:
        command.extend(["-f", str(values_file)])
    command.extend(extra_args)
    return subprocess.run(command, capture_output=True, text=True, check=False)


def rendered_documents(values_file):
    result = helm_template(values_file)
    if result.returncode != 0:
        raise AssertionError(f"helm template failed:\n{result.stderr}")
    return [document for document in yaml.safe_load_all(result.stdout) if document]


def one_resource(documents, kind):
    matches = [document for document in documents if document.get("kind") == kind]
    if len(matches) != 1:
        raise AssertionError(f"expected one {kind}, got {len(matches)}")
    return matches[0]


class MessagePitChartRenderTests(unittest.TestCase):
    def setUp(self):
        self.managed_values = CHART / "ci" / "test-values.yaml"
        self.external_values = CHART / "tests" / "existing-secret-values.yaml"
        self.network_policy_values = CHART / "tests" / "network-policy-values.yaml"

    def test_managed_credentials_render_secure_single_pod_workload(self):
        documents = rendered_documents(self.managed_values)

        self.assertEqual(
            ["Deployment", "Secret", "Service", "ServiceAccount"],
            sorted(document["kind"] for document in documents),
        )

        secret = one_resource(documents, "Secret")
        self.assertEqual("test-sendgrid-key", secret["stringData"]["MP_SENDGRID_API_KEY"])
        self.assertEqual("e2e:test-password", secret["stringData"]["MP_UI_AUTH"])

        deployment = one_resource(documents, "Deployment")
        self.assertEqual(1, deployment["spec"]["replicas"])
        self.assertEqual(
            {"maxSurge": 0, "maxUnavailable": 1},
            deployment["spec"]["strategy"]["rollingUpdate"],
        )
        container = deployment["spec"]["template"]["spec"]["containers"][0]
        self.assertEqual(PINNED_IMAGE, container["image"])
        self.assertEqual(["--twilio=", "--webhook=", "--pop3="], container["args"])
        self.assertEqual(
            {"ui": 8025, "sendgrid": 8100},
            {port["name"]: port["containerPort"] for port in container["ports"]},
        )
        self.assertEqual(
            {"MP_MAX_AGE": "24h", "MP_MAX_MESSAGES": "10000"},
            {
                item["name"]: item["value"]
                for item in container["env"]
                if "value" in item
            },
        )
        secret_refs = {
            item["name"]: item["valueFrom"]["secretKeyRef"]
            for item in container["env"]
            if "valueFrom" in item
        }
        self.assertEqual(
            {"name": "test-messagepit", "key": "MP_SENDGRID_API_KEY"},
            secret_refs["MP_SENDGRID_API_KEY"],
        )
        self.assertEqual(
            {"name": "test-messagepit", "key": "MP_UI_AUTH"},
            secret_refs["MP_UI_AUTH"],
        )
        self.assertEqual(
            {
                "allowPrivilegeEscalation": False,
                "capabilities": {"drop": ["ALL"]},
                "readOnlyRootFilesystem": True,
                "runAsGroup": 65532,
                "runAsNonRoot": True,
                "runAsUser": 65532,
            },
            container["securityContext"],
        )
        self.assertEqual(
            ["/messagepit", "readyz"],
            container["readinessProbe"]["exec"]["command"],
        )
        self.assertEqual(
            ["/messagepit", "readyz"],
            container["startupProbe"]["exec"]["command"],
        )
        self.assertEqual(
            {"path": "/healthz", "port": "ui"},
            container["livenessProbe"]["httpGet"],
        )

        service = one_resource(documents, "Service")
        self.assertEqual("ClusterIP", service["spec"]["type"])
        self.assertEqual(
            {"ui": (8025, "ui"), "sendgrid": (8100, "sendgrid")},
            {
                port["name"]: (port["port"], port["targetPort"])
                for port in service["spec"]["ports"]
            },
        )

    def test_existing_secret_is_referenced_without_rendering_a_secret(self):
        documents = rendered_documents(self.external_values)
        self.assertFalse(any(document["kind"] == "Secret" for document in documents))
        deployment = one_resource(documents, "Deployment")
        container = deployment["spec"]["template"]["spec"]["containers"][0]
        secret_names = {
            item["valueFrom"]["secretKeyRef"]["name"]
            for item in container["env"]
            if "valueFrom" in item
        }
        self.assertEqual({"shared-messagepit-credentials"}, secret_names)

    def test_credentials_are_required_when_chart_manages_the_secret(self):
        result = helm_template()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("sendgrid.apiKey is required", result.stderr)

    def test_network_policy_is_opt_in_and_restricts_service_ports(self):
        default_documents = rendered_documents(self.managed_values)
        self.assertFalse(any(document["kind"] == "NetworkPolicy" for document in default_documents))

        documents = rendered_documents(self.network_policy_values)
        policy = one_resource(documents, "NetworkPolicy")
        ingress = policy["spec"]["ingress"][0]
        self.assertEqual(2, len(ingress["from"]))
        self.assertEqual(
            {8025, 8100},
            {port["port"] for port in ingress["ports"]},
        )

    def test_schema_rejects_more_than_one_replica(self):
        result = helm_template(self.managed_values, "--set", "replicaCount=2")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("replicaCount", result.stderr)


if __name__ == "__main__":
    unittest.main()

# MessagePit Email Chart Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a production-safe Helm chart that deploys one stock MessagePit pod as a private SendGrid-compatible email sink while leaving Twilio unchanged.

**Architecture:** A one-replica Deployment runs MessagePit with in-memory bounded storage. A ClusterIP Service exposes only the SendGrid and inbox ports, credentials come from a chart-managed or existing Secret, and an optional NetworkPolicy limits ingress.

**Tech Stack:** Helm 3/4 templates, Kubernetes `apps/v1`, Python `unittest` with PyYAML, MessagePit 1.3.0.

## Global Constraints

- Deploy exactly one MessagePit replica; multiple replicas would create split inboxes.
- Pin `ghcr.io/coreydaley/messagepit:1.3.0` with digest `sha256:04bd1a2f82c8b90aec52c6bfa4090ef1088acb025f5193f75112207886ef0a02`.
- Expose only UI/API port `8025` and SendGrid port `8100` through a ClusterIP Service.
- Keep Twilio disabled and leave `TWILIO_API_URL` unset in Identity.
- Require SendGrid bearer authentication and UI/API basic authentication.
- Use in-memory storage with a default maximum age of `24h` and maximum count of `10000`.
- Do not add an Ingress, persistent volume, Twilio adapter, or Identity/E2E code change.

---

### Task 1: Render contract tests

**Files:**
- Create: `charts/messagepit/tests/test_render.py`
- Create: `charts/messagepit/ci/test-values.yaml`
- Create: `charts/messagepit/tests/existing-secret-values.yaml`
- Create: `charts/messagepit/tests/network-policy-values.yaml`

**Interfaces:**
- Consumes: Helm CLI and the future `charts/messagepit` chart.
- Produces: Executable render assertions for chart-managed credentials, existing Secrets, security settings, probes, service ports, and NetworkPolicy behavior.

- [ ] **Step 1: Write the failing render tests**

Create a `unittest.TestCase` that runs:

```python
subprocess.run(
    ["helm", "template", "test", CHART, "-f", values_file],
    check=True,
    capture_output=True,
    text=True,
)
```

Parse documents with `yaml.safe_load_all`. Assert that managed values render one `Secret`, an external Secret renders none, the Deployment references the correct secret keys, the service exposes exactly `ui:8025` and `sendgrid:8100`, the stock image uses the pinned digest, probes and security context exist, unused listeners are disabled, and NetworkPolicy is opt-in.

- [ ] **Step 2: Run the tests and verify RED**

Run:

```bash
python3 -m unittest discover -s charts/messagepit/tests -v
```

Expected: FAIL because `charts/messagepit/Chart.yaml` and templates do not exist.

- [ ] **Step 3: Commit the failing contract tests**

```bash
git add charts/messagepit/tests charts/messagepit/ci
git commit -m "test: define MessagePit chart render contract"
```

### Task 2: Chart metadata, values, helpers, and credentials

**Files:**
- Create: `charts/messagepit/Chart.yaml`
- Create: `charts/messagepit/values.yaml`
- Create: `charts/messagepit/values.schema.json`
- Create: `charts/messagepit/templates/_helpers.tpl`
- Create: `charts/messagepit/templates/serviceaccount.yaml`
- Create: `charts/messagepit/templates/secret.yaml`

**Interfaces:**
- Consumes: Values `image`, `sendgrid`, `ui`, `existingSecret`, `serviceAccount`, and standard pod scheduling options.
- Produces: `messagepit.fullname`, `messagepit.labels`, `messagepit.selectorLabels`, `messagepit.serviceAccountName`, and `messagepit.secretName` template helpers.

- [ ] **Step 1: Add chart metadata and secure defaults**

Set chart version `0.1.0`, app version `1.3.0`, replica count `1`, the pinned image digest, bounded retention, restrictive container security defaults, and empty credential values. The JSON schema must reject replica counts other than one and invalid digest formats.

- [ ] **Step 2: Add reusable helpers and ServiceAccount**

Follow Kubernetes recommended labels and the repository's `e10s-engine-sync` naming behavior. Allow `serviceAccount.create=false` with a supplied name.

- [ ] **Step 3: Add Secret selection**

When `existingSecret` is empty, render an opaque Secret with:

```yaml
stringData:
  MP_SENDGRID_API_KEY: {{ required "sendgrid.apiKey is required" .Values.sendgrid.apiKey }}
  MP_UI_AUTH: {{ required "ui.auth is required" .Values.ui.auth }}
```

When `existingSecret` is set, render no Secret and return that name from `messagepit.secretName`.

- [ ] **Step 4: Run render tests**

Expected: tests still fail only for missing Deployment, Service, and NetworkPolicy resources.

- [ ] **Step 5: Commit chart foundations**

```bash
git add charts/messagepit
git commit -m "feat: add MessagePit chart foundations"
```

### Task 3: MessagePit workload and networking

**Files:**
- Create: `charts/messagepit/templates/deployment.yaml`
- Create: `charts/messagepit/templates/service.yaml`
- Create: `charts/messagepit/templates/networkpolicy.yaml`
- Create: `charts/messagepit/templates/NOTES.txt`

**Interfaces:**
- Consumes: Helpers and values from Task 2.
- Produces: The runnable MessagePit Deployment, internal Service endpoints, and optional ingress restrictions.

- [ ] **Step 1: Add the Deployment**

Render one container with the pinned digest, explicit `ui` and `sendgrid` ports, credentials from `messagepit.secretName`, retention environment variables, and arguments that disable Twilio, webhook capture, and POP3. Use `/messagepit readyz` for startup/readiness and `GET /healthz` on the `ui` port for liveness.

- [ ] **Step 2: Add the ClusterIP Service**

Expose exactly:

```yaml
- name: ui
  port: 8025
  targetPort: ui
- name: sendgrid
  port: 8100
  targetPort: sendgrid
```

- [ ] **Step 3: Add optional NetworkPolicy**

When `networkPolicy.enabled=true`, select only this release's pods and render the caller-provided ingress rules for ports `ui` and `sendgrid`. Do not invent cluster-specific namespace labels.

- [ ] **Step 4: Add NOTES output**

Print the cluster-local SendGrid base URL and UI/API URL. Remind operators that Twilio remains unchanged.

- [ ] **Step 5: Run render tests and verify GREEN**

```bash
python3 -m unittest discover -s charts/messagepit/tests -v
```

Expected: all render contract tests pass.

- [ ] **Step 6: Commit workload resources**

```bash
git add charts/messagepit/templates
git commit -m "feat: deploy MessagePit email sink"
```

### Task 4: Operator documentation and final verification

**Files:**
- Create: `charts/messagepit/README.md`

**Interfaces:**
- Consumes: The finished chart values and generated Service names.
- Produces: Installation, Identity configuration, existing-Secret, NetworkPolicy, and rollback instructions.

- [ ] **Step 1: Document installation and configuration**

Include chart-managed and existing-Secret examples, the `SENDGRID_BASE_URL` value, the requirement to leave `TWILIO_API_URL` unset, credential rotation, and the consequences of in-memory storage.

- [ ] **Step 2: Run Helm validation**

```bash
helm lint charts/messagepit -f charts/messagepit/ci/test-values.yaml
helm template test charts/messagepit -f charts/messagepit/ci/test-values.yaml
helm template test charts/messagepit -f charts/messagepit/tests/existing-secret-values.yaml
helm template test charts/messagepit -f charts/messagepit/tests/network-policy-values.yaml
```

Expected: all commands exit zero and no credential value appears in non-Secret resources.

- [ ] **Step 3: Run the container security smoke test**

Run the stock image as UID/GID `65532`, with a read-only root filesystem and the chart's arguments/environment. Confirm `/messagepit readyz` succeeds and authenticated SendGrid returns `202`.

- [ ] **Step 4: Run all render tests again**

```bash
python3 -m unittest discover -s charts/messagepit/tests -v
```

Expected: all tests pass.

- [ ] **Step 5: Review the diff and commit documentation**

```bash
git diff --check
git status --short
git add charts/messagepit/README.md docs/superpowers/plans/2026-08-09-messagepit-email-chart.md
git commit -m "docs: explain MessagePit email deployment"
```

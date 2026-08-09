# MessagePit

This chart deploys [MessagePit](https://github.com/coreydaley/messagepit) as a private SendGrid-compatible email sink for Frontegg testing. The first release handles email only. It does not redirect Twilio Messaging or Twilio Verify.

## Architecture

The chart creates one MessagePit Deployment and one ClusterIP Service:

| Service port | Purpose | Consumer |
| --- | --- | --- |
| `8100` | SendGrid v3 `POST /v3/mail/send` | Identity |
| `8025` | Inbox UI and management API | E2E runners and authorized operators |

The mailbox uses a pod-local temporary SQLite database. Restarting or replacing the pod clears all captured messages. The chart enforces one replica because separate MessagePit pods would have separate inboxes.

Twilio remains unchanged by default. Do not set `TWILIO_API_URL` until an adapter sidecar has been built and enabled.

## Sidecar-ready Twilio adapter

The chart does not ship adapter code or start another container by default. It provides the wiring so a future adapter can be enabled using only a values file:

```yaml
messagepit:
  twilioIngest:
    enabled: true

sidecars:
  - name: twilio-adapter
    image: ghcr.io/frontegg/messagepit-twilio-adapter:<tag-or-digest>
    ports:
      - name: twilio-adapter
        containerPort: 8201
        protocol: TCP
    env:
      - name: MESSAGEPIT_TWILIO_URL
        value: http://127.0.0.1:8200

service:
  extraPorts:
    - name: twilio
      port: 8200
      targetPort: twilio-adapter
      protocol: TCP
```

Both containers run in the same pod and share its network namespace. MessagePit binds its native Twilio ingest endpoint to `127.0.0.1:8200`, so only the adapter can reach it. Identity calls the adapter through the Service; with the example above its URL is:

```text
http://messagepit.messaging-test.svc.cluster.local:8200
```

The adapter may use `extraVolumes` and normal container `volumeMounts` when it needs configuration or certificates. If NetworkPolicy is enabled, each `service.extraPorts` target is automatically permitted for the configured callers.

## Install with an existing Secret

Create a Secret containing both required keys:

```bash
kubectl create secret generic messagepit-credentials \
  --from-literal=MP_SENDGRID_API_KEY='<sendgrid-test-key>' \
  --from-literal=MP_UI_AUTH='<username>:<password>'
```

Install the chart:

```bash
helm upgrade --install messagepit ./charts/messagepit \
  --namespace messaging-test \
  --create-namespace \
  --set existingSecret=messagepit-credentials
```

The Secret must be in the same namespace as the Helm release.

## Install with a chart-managed Secret

Use an environment-specific values file that is stored securely and is not committed:

```yaml
sendgrid:
  apiKey: <sendgrid-test-key>

ui:
  auth: <username>:<password>
```

```bash
helm upgrade --install messagepit ./charts/messagepit \
  --namespace messaging-test \
  --create-namespace \
  --values messagepit-secrets.yaml
```

Using `existingSecret` is preferred because Helm release metadata otherwise contains the chart-managed credential values.

## Configure Identity

For an Identity deployment in the same cluster, set:

```text
SENDGRID_BASE_URL=http://messagepit.messaging-test.svc.cluster.local:8100
SENDGRID_API_KEY=<same value as MP_SENDGRID_API_KEY>
```

If the Helm release name differs from `messagepit`, use the Service name printed by `helm get notes`.

Leave `TWILIO_API_URL` unset so all Twilio traffic continues to use the real provider.

## Temporary venv cluster test with kubectl

Assuming “venv” means a Frontegg virtual test environment backed by Kubernetes, yes: install MessagePit into that cluster and temporarily change the running Identity Deployment. This is suitable for a large manual test before the environment's Helm values are updated permanently.

First select the venv cluster and verify it before making changes:

```bash
kubectl config use-context <venv-context>
kubectl config current-context
kubectl get namespace
```

Install the chart and wait for its pod:

```bash
helm upgrade --install messagepit ./charts/messagepit \
  --namespace messaging-test \
  --create-namespace \
  --set existingSecret=messagepit-credentials \
  --wait

kubectl --namespace messaging-test get pods,service
```

Then point Identity at the in-cluster Service. Use the real Identity namespace and Deployment name from `kubectl get deployment --all-namespaces`:

```bash
kubectl --namespace <identity-namespace> set env deployment/<identity-deployment> \
  SENDGRID_BASE_URL=http://messagepit.messaging-test.svc.cluster.local:8100 \
  SENDGRID_API_KEY=<same-value-as-MP_SENDGRID_API_KEY>

kubectl --namespace <identity-namespace> rollout status deployment/<identity-deployment>
```

This changes the Deployment template and Kubernetes creates new Identity pods with the override. It does not change Identity code. Confirm the values and test one email before running the full suite:

```bash
kubectl --namespace <identity-namespace> set env deployment/<identity-deployment> --list
kubectl --namespace messaging-test port-forward service/messagepit 8025:8025
```

Open `http://127.0.0.1:8025` and authenticate with `MP_UI_AUTH` to inspect captured messages.

The `kubectl set env` change is temporary when Argo CD, Helm, or another controller manages Identity; reconciliation may restore the declared configuration. Pause automatic sync for the test or put the same override in the venv values if it is immediately reverted. Before changing anything, save the current Deployment YAML or record whether these variables already exist. To roll back an override that was previously absent:

```bash
kubectl --namespace <identity-namespace> set env deployment/<identity-deployment> \
  SENDGRID_BASE_URL- SENDGRID_API_KEY-

kubectl --namespace <identity-namespace> rollout status deployment/<identity-deployment>
```

Do not remove `SENDGRID_API_KEY` during rollback if the environment already had one; restore its original Secret-backed configuration instead.

## Configure E2E inbox access

The inbox API is available at:

```text
http://messagepit.messaging-test.svc.cluster.local:8025/api/v1
```

Clients must use HTTP Basic authentication with the username and password stored in `MP_UI_AUTH`.

## Restrict callers with NetworkPolicy

NetworkPolicy is disabled by default because namespace and pod labels differ between clusters. Enable it with the exact caller selectors for the target environment:

```yaml
networkPolicy:
  enabled: true
  ingressFrom:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: identity-test
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: e2e-runners
```

When enabled, the policy permits selected callers to reach only ports `8025` and `8100`. An empty `ingressFrom` is rejected during rendering.

## Retention and resources

Defaults:

```yaml
retention:
  maxAge: 24h
  maxMessages: 10000

storage:
  sizeLimit: 1Gi

resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    memory: 256Mi
```

MessagePit prunes the oldest messages when either bound is exceeded.

The temporary database is stored in a bounded `emptyDir` mounted at `/tmp`. This keeps the container root filesystem read-only while making pod replacement intentionally clear the inbox.

## Validation

```bash
python3 -m unittest discover -s charts/messagepit/tests -v
helm lint charts/messagepit -f charts/messagepit/ci/test-values.yaml
helm template test charts/messagepit -f charts/messagepit/ci/test-values.yaml
helm template test charts/messagepit -f charts/messagepit/tests/existing-secret-values.yaml
helm template test charts/messagepit -f charts/messagepit/tests/network-policy-values.yaml
helm template test charts/messagepit -f charts/messagepit/tests/sidecar-values.yaml
```

## Rollback

Unset `SENDGRID_BASE_URL` in Identity to restore the SendGrid SDK's normal endpoint. After Identity has rolled back, remove the sink with:

```bash
helm uninstall messagepit --namespace messaging-test
```

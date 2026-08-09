# MessagePit

This chart deploys [MessagePit](https://github.com/coreydaley/messagepit) as a private SendGrid-compatible email sink for Frontegg testing. The first release handles email only. It does not redirect Twilio Messaging or Twilio Verify.

## Architecture

The chart creates one MessagePit Deployment and one ClusterIP Service:

| Service port | Purpose | Consumer |
| --- | --- | --- |
| `8100` | SendGrid v3 `POST /v3/mail/send` | Identity |
| `8025` | Inbox UI and management API | E2E runners and authorized operators |

The mailbox uses a pod-local temporary SQLite database. Restarting or replacing the pod clears all captured messages. The chart enforces one replica because separate MessagePit pods would have separate inboxes.

Twilio remains unchanged. Do not set `TWILIO_API_URL` when rolling out this chart.

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
```

## Rollback

Unset `SENDGRID_BASE_URL` in Identity to restore the SendGrid SDK's normal endpoint. After Identity has rolled back, remove the sink with:

```bash
helm uninstall messagepit --namespace messaging-test
```

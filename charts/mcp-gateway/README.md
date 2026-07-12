# Frontegg MCP Gateway Helm Chart

A Helm chart for self-hosting Frontegg's **MCP Gateway** on Kubernetes. It packages
the two services that provide an MCP-compliant authorization and tool-routing layer
in front of your MCP servers.

> Official guide: <https://developers.frontegg.com/agen-for-saas/configuration/hosting-mcp-gateway>

## Components

| Service    | Deployment / Service name    | Role |
|------------|------------------------------|------|
| `mcp-auth` | `<release>-mcp-gateway-auth` | OAuth, dynamic client registration (DCR), authorization, token issuance, integration/step-up callbacks. |
| `mcp-gw`   | `<release>-mcp-gateway-gw`   | Receives MCP requests and routes/authorizes them against Frontegg. |

Both listen on container port **8080**, share a **Redis** backend for token/session
caching, and sit behind a single external hostname (only the path differs).

## What the chart deploys

- A Deployment + ClusterIP Service for `mcp-auth`
- A Deployment + ClusterIP Service for `mcp-gw`
- A shared ServiceAccount (created by default; toggle with `serviceAccount.create`)
- Optional HorizontalPodAutoscaler per component (disabled by default)

The chart ships **no Ingress or L7 router** — front the two services with your own
ingress / API gateway (NGINX, Traefik, Istio, Envoy, AWS ALB, GCP HTTPS LB, Kong, …).

## Installation

```bash
helm repo add frontegg https://frontegg.github.io/helm-charts/
helm repo update

helm upgrade --install mcp-gateway frontegg/mcp-gateway -f my-values.yaml
```

Minimal `my-values.yaml`:

```yaml
env:
  redisHost: "my-redis.internal"
  redisPassword: "<redis-password>"
  fronteggRegion: "eu"                                 # eu | us | ca | au | stg
  vendorClientId: "<frontegg-vendor-client-id>"
  vendorClientSecret: "<frontegg-vendor-client-secret>"
  applicationId: "<frontegg-application-id>"
  fronteggMcpGwHost: "mcp.example.com"                 # external host, no scheme
  externalAuthorizationUrl: "https://mcp.example.com"  # same host, with scheme
  hybridAuthHost: "https://auth.example.com"
```

To keep secrets out of your values file, put them in a Secret you manage yourself and
reference it with `existingSecret` — see [Configuration](#configuration).

## Routing

Configure your ingress/API gateway with the path map below. Route the auth paths to
**`<release>-mcp-gateway-auth`**; send **everything else** to **`<release>-mcp-gateway-gw`**.

| Path                                          | Method | Target       |
|-----------------------------------------------|--------|--------------|
| `/.well-known/oauth-protected-resource`       | GET    | `mcp-auth`   |
| `/.well-known/oauth-authorization-server`     | GET    | `mcp-auth`   |
| `/authorize`                                  | GET    | `mcp-auth`   |
| `/dcr/register`                               | POST   | `mcp-auth`   |
| `/token`                                      | POST   | `mcp-auth`   |
| `/integration-callback`                       | GET    | `mcp-auth`   |
| `/security-stepup-verify`                     | GET    | `mcp-auth`   |
| `/external-mcp/authorize`                     | GET    | `mcp-auth`   |
| `/external-mcp/callback`                      | GET    | `mcp-auth`   |
| Everything else (`/`)                         | *      | `mcp-gw`     |

Router requirements:

- **Specificity/order:** auth paths must take priority over the catch-all `/` (declare them first on order-based routers).
- **Host header preservation:** the incoming `Host` must match `env.fronteggMcpGwHost` — both services use it to validate issuer URLs.
- **Single external hostname:** both services share one external host.

## Configuration

Keys under `env` are camelCase and converted to `UPPER_SNAKE_CASE` environment variables
(e.g. `vendorClientId` → `VENDOR_CLIENT_ID`). Every key under `env` is injected into
**both** deployments, rendered inline as `value:` on the containers.

For secrets, you have two options:

- **Inline under `env`** — simplest; the value lives in your Helm values (and the Helm
  release, stored in the cluster). Fine for quick start / dev.
- **`existingSecret`** — name of a Secret you manage **outside** this chart (External
  Secrets Operator, sealed-secrets, `kubectl create secret`, …). When set, it's loaded
  into both deployments via `envFrom`, keeping secret material out of Helm entirely.
  Its keys must already be `UPPER_SNAKE_CASE` env var names (e.g. `REDIS_PASSWORD`), and
  the Secret must exist in the release namespace before the pods start. Recommended for
  production. See [Referencing an existing Secret](#referencing-an-existing-secret).

### Required environment (`env`)

| Key                        | Default   | Description |
|----------------------------|-----------|-------------|
| `redisHost`                | `""`      | Hostname of the shared Redis instance. |
| `redisPort`                | `"6379"`  | Redis port. |
| `redisPassword`            | `""`      | Redis password. |
| `redisDb`                  | `"0"`     | Redis database index. |
| `redisTlsEnabled`          | `"true"`  | Set `"false"` for plaintext Redis. |
| `cacheTtl`                 | `"300"`   | Token/session cache TTL (seconds). |
| `fronteggRegion`           | `"eu"`    | `eu` \| `us` \| `ca` \| `au` \| `stg`. |
| `vendorClientId`           | `""`      | Frontegg vendor client ID. |
| `vendorClientSecret`       | `""`      | Frontegg vendor client secret. |
| `applicationId`            | `""`      | Frontegg application ID. |
| `fronteggMcpGwHost`        | `""`      | External hostname of the gateway, **without** scheme. |
| `externalAuthorizationUrl` | `""`      | Same hostname **with** scheme; published as the OAuth issuer. |
| `hybridAuthHost`           | `""`      | URL of your hybrid auth service, with scheme. |

### Optional environment (`env`, commented out by default)

| Key                          | Description |
|------------------------------|-------------|
| `secretEncryptionKey`        | 32-byte key to decrypt integration secrets (client secrets & API keys) the control plane delivers encrypted. See [Integration secret encryption](#integration-secret-encryption). |
| `approvalFlowWebhookEndpoint`| Webhook that receives tool-call approval requests. |
| `eventStdoutEnabled`         | `"true"` emits events to **stdout** as newline-delimited JSON (see [Event delivery](#event-delivery)). |
| `eventWebhookProvider`       | Where to forward audit events: `datadog` \| `splunk` \| `coralogix` \| `webhook`. |
| `eventWebhookUrl`            | Destination URL for the event webhook. |
| `eventWebhookSecret`         | Secret used to authorize event webhook deliveries. |

To add any other env var, just add a key under `env`.

### Referencing an existing Secret

To keep sensitive values out of Helm, create a Secret whose keys are the final
`UPPER_SNAKE_CASE` env var names and point `existingSecret` at it:

```bash
kubectl create secret generic my-mcp-secrets \
  --from-literal=REDIS_PASSWORD='...' \
  --from-literal=SECRET_ENCRYPTION_KEY='...'
```

```yaml
existingSecret: "my-mcp-secrets"
```

The Secret is loaded into both deployments via `envFrom`:

```yaml
envFrom:
  - secretRef:
      name: my-mcp-secrets
```

The chart does not create or manage this Secret — it must exist in the release
namespace before the pods start, or they fail with `CreateContainerConfigError`.

Only **non-empty** `env` values are rendered inline; an empty/unset `env` key (like the
default `redisPassword: ""`) is omitted entirely, so the same key from `existingSecret`
takes effect. If you set a key to a non-empty value under `env` **and** in the Secret,
the inline `env` value wins (a container `env.value` overrides `envFrom`) — so to source
a value from the Secret, leave its `env` key empty or unset.

Changing the Secret does **not** restart the pods automatically —
run `kubectl rollout restart deploy/<release>-mcp-gateway-auth deploy/<release>-mcp-gateway-gw`
(or use a controller like Stakater Reloader).

### Event delivery

Non-raw events are delivered to **one** sink:

- **Webhook** — set `eventWebhookProvider` + `eventWebhookUrl` (+ `eventWebhookSecret`). Events are POSTed to your Datadog/Splunk/Coralogix/generic endpoint.
- **stdout** — set `eventStdoutEnabled: "true"`. Each event is written to the pod's stdout as one JSON line, tagged with a stable discriminator so a log collector (OTEL Collector, Fluent Bit, Vector) can scrape it out of the log stream:

  ```json
  {"stream":"mcp-gw-events","event":{"eventDomain":"...","origin":"mcp-gw","context":{...},"subject":{...},"payload":{...}}}
  ```

  Needs no external webhook infrastructure. Example OTEL Collector filter to keep only gateway events:

  ```yaml
  processors:
    filter/events:
      logs:
        log_record:
          - 'body["stream"] != "mcp-gw-events"'   # drop everything else
  ```

  Events are written directly to stdout (not through the app logger), so they are **not** affected by `LOG_LEVEL` / `SILENT_LOG`.

### Integration secret encryption

For hybrid (on-prem) deployments, set `secretEncryptionKey` to enable end-to-end
encryption of integration secrets (OAuth **client secrets** and **API keys**). When
configured, the Frontegg control plane delivers them **encrypted** and the gateway
decrypts on read, in memory — they are never written to your Redis cache in cleartext.

- Algorithm: **AES-256-GCM**, format `v2:<iv_hex>:<authTag_hex>:<ciphertext_hex>`.
- The key must be a **32-character string** (used verbatim as the AES-256 key — **not** a Base64/hex-encoded 32-byte value, which would be longer and fail with `Invalid key length`) and **identical** to the one the control plane encrypts with.
- Values without the `v2:` prefix are passed through unchanged, so it can be rolled out gradually.

To keep the key out of Helm values, provide it as `SECRET_ENCRYPTION_KEY` in an
`existingSecret` (see [Referencing an existing Secret](#referencing-an-existing-secret))
instead of setting `secretEncryptionKey` inline.

### Common values

| Key                                             | Default | Description |
|-------------------------------------------------|---------|-------------|
| `mcpAuth.repository` / `mcpGw.repository`        | Frontegg ECR | Container images (managed by Frontegg). |
| `mcpAuth.tag` / `mcpGw.tag`                       | pinned  | **Do not override** — upgrade the chart version to pick up new images. |
| `mcpAuth.port` / `mcpGw.port`                     | `8080`  | Container/Service port. |
| `mcpAuth.resources` / `mcpGw.resources`           | 200m CPU / 256Mi req, 512Mi limit | Per-component resources. |
| `service.type`                                    | `ClusterIP` | Service type for both components. |
| `autoscaling.mcpAuth` / `autoscaling.mcpGw`       | `enabled: false`, 1–100 replicas @ 80% CPU | Per-component HPA. When enabled, the Deployment's `replicas` is omitted so the HPA manages it. |
| `serviceAccount.create` / `serviceAccount.name`   | `true` / `""` | Set `create: false` + `name` to reuse an existing SA. |
| `nodeSelector`, `tolerations`, `affinity`, `podAnnotations`, `podLabels`, `podSecurityContext`, `securityContext` | `{}` / `[]` | Applied to **both** deployments. |
| `imagePullSecrets`, `volumes`, `volumeMounts`     | `[]`    | Standard pod-level options. |

Enable autoscaling per component:

```yaml
autoscaling:
  mcpGw:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
```

## Verification

```bash
kubectl rollout status deploy/<release>-mcp-gateway-auth
kubectl rollout status deploy/<release>-mcp-gateway-gw

# Health checks — both should return 200 on GET /health.
kubectl port-forward svc/<release>-mcp-gateway-auth 8080:8080 &
curl -fsS http://localhost:8080/health
kubectl port-forward svc/<release>-mcp-gateway-gw 8081:8080 &
curl -fsS http://localhost:8081/health
```

## Upgrading

Image versions are tied to chart versions; there are no CRDs and the chart owns no
persistent state (Redis lives externally).

```bash
helm repo update
helm upgrade mcp-gateway frontegg/mcp-gateway --version <new-chart-version> -f my-values.yaml
```

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
  fronteggMcpGwHost: "<id>.mcp-gw.frontegg.com"  # your Frontegg cloud MCP gateway host, no scheme
  hybridAuthHost: "https://mcp.example.com"      # public URL clients use to reach this gateway
```

To keep secrets out of your values file, put them in a Secret you manage yourself and
reference it with `existingSecret` — see [Configuration](#configuration).

### Registry access

Frontegg publishes the images to Docker Hub and to Amazon ECR. Pick one with `imageSource`:

| `imageSource` | Images pulled from | Authentication |
|---|---|---|
| `dockerhub` (default) | `docker.io/fronteggcustomers` | Pull secret with the token Frontegg gives you |
| `ecr` | Frontegg's Amazon ECR (`us-east-1`) | Your nodes' IAM role, once Frontegg has granted your AWS account access |
| `custom` | `imageRegistry`, your own mirror | Whatever your mirror needs |

#### Docker Hub (default)

Create a pull secret in the release namespace and reference it from your values:

```bash
kubectl create secret docker-registry frontegg-registry \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=fronteggcustomers \
  --docker-password='<token from Frontegg>'
```

```yaml
imagePullSecrets:
  - name: frontegg-registry
```

Use `https://index.docker.io/v1/` as `--docker-server`: kubelet falls back to that key for
Docker Hub images, so the secret works with or without the `docker.io/` host prefix.

#### Amazon ECR (AWS)

Send Frontegg the AWS account ID your cluster runs in; Frontegg grants it pull access. Then:

```yaml
imageSource: ecr
```

No `imagePullSecrets`: EKS nodes pull with their IAM role. The managed policy
`AmazonEC2ContainerRegistryReadOnly` on the node role is enough.

#### Your own registry

Mirror `hybrid-agen-co-auth` and `hybrid-agen-co-gw` (same names and tags) into your registry,
for example with an ECR pull-through cache of the Docker Hub organization, and set:

```yaml
imageSource: custom
imageRegistry: registry.example.com/frontegg   # images: <imageRegistry>/hybrid-agen-co-{auth,gw}
```

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
| `/external-mcp/authorize`                     | GET    | `mcp-auth`   |
| `/external-mcp/callback`                      | GET    | `mcp-auth`   |
| `/external-mcp/callback/complete`             | POST   | `mcp-auth`   |
| Everything else (`/`)                         | *      | `mcp-gw`     |

Router requirements:

- **Specificity/order:** auth paths must take priority over the catch-all `/` (declare them first on order-based routers).
- **Host header preservation:** pass the original `Host` through. It must be the host of `env.hybridAuthHost`, the public URL clients connect to; the services build the OAuth protected-resource metadata from it.
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
| `fronteggMcpGwHost`        | `""`      | Your **Frontegg cloud** MCP gateway host, **without** scheme (for example `<id>.mcp-gw.frontegg.com`). The gateway reads your signing keys and feature flags from it and publishes `https://<fronteggMcpGwHost>` to MCP clients as the OAuth authorization server. Not the host this chart is served on. |
| `hybridAuthHost`           | `""`      | Public URL clients use to reach this gateway, with scheme (for example `https://mcp.example.com`). Integration OAuth callbacks and step-up links point here. |

Both pods check these at startup: without `fronteggMcpGwHost` they log `FRONTEGG_MCP_GW_HOST env var is required` and exit; without `hybridAuthHost` they log an error and keep running, but integration OAuth callbacks fail.

### Optional environment (`env`, commented out by default)

| Key                          | Description |
|------------------------------|-------------|
| `secretEncryptionKey`        | 32-byte key to decrypt integration secrets (client secrets & API keys) the control plane delivers encrypted. See [Integration secret encryption](#integration-secret-encryption). |
| `approvalFlowWebhookEndpoint`| Webhook that receives tool-call approval requests. |
| `eventStdoutEnabled`         | `"true"` emits events to **stdout** as newline-delimited JSON (see [Event delivery](#event-delivery)). |
| `eventWebhookProvider`       | Where to forward audit events: `datadog` \| `splunk` \| `coralogix` \| `webhook`. |
| `eventWebhookUrl`            | Destination URL for the event webhook. |
| `eventWebhookSecret`         | Secret used to authorize event webhook deliveries. |
| `hybridCacheMaxStalenessSeconds` | How long cached control-plane data keeps being served while the control plane is unavailable. Default `"86400"` (24h); `"0"` disables it. See [Control plane outages](#control-plane-outages). |
| `toolSearchMode`             | `cloud` (default) searches tools in the control plane and locally while it is unavailable; `local` only searches locally. See [Local tool search](#local-tool-search). |
| `externalAuthorizationUrl`   | **Deprecated.** Read only when `fronteggMcpGwHost` is unset, as the source of that host. The authorization server is always `https://<fronteggMcpGwHost>`. |

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

### Control plane outages

The gateway caches control-plane data (tools, policies, configuration) in your Redis. If
the control plane is unavailable when the cache is due for a refresh, the gateway keeps
serving the last data it fetched, for up to `hybridCacheMaxStalenessSeconds` (24h by
default). Requests to the control plane time out after 10 seconds, so an unresponsive
control plane falls back to the cache instead of stalling requests.

### Local tool search

`mcp-gw` can search tools itself, with the same embedding model and ranking as the
control plane, from a search index it caches in your Redis:

- `toolSearchMode: "cloud"` (default) — searches in the control plane, and locally while
  it is unavailable.
- `toolSearchMode: "local"` — only searches locally; queries never leave your network.
  Searches fail, rather than fall back to the control plane, if local search is unavailable.

The embedding model (about 23 MB) is downloaded on the first local search, so `mcp-gw`
needs outbound HTTPS access to `huggingface.co`. Files are verified by checksum.

Only needed if you run with `readOnlyRootFilesystem: true`: the model is written under
`/tmp`, which is then read-only, so mount a writable volume there. With the chart's
defaults `/tmp` is writable and nothing is needed.

```yaml
volumes:
  - name: tmp
    emptyDir: {}
volumeMounts:
  - name: tmp
    mountPath: /tmp
```

Loading the model adds about 90 MB of memory to an `mcp-gw` pod, which the default
`mcpGw.resources` account for.

### Common values

| Key                                             | Default | Description |
|-------------------------------------------------|---------|-------------|
| `imageSource`                                     | `dockerhub` | Where both images come from: `dockerhub`, `ecr` or `custom` — see [Registry access](#registry-access). |
| `imageRegistry`                                   | `""`    | Registry and namespace for `imageSource: custom` (`<imageRegistry>/hybrid-agen-co-{auth,gw}`). |
| `mcpAuth.repository` / `mcpGw.repository`        | `""`    | Full image path without tag for one image; overrides `imageSource`. Leave empty unless you mirror the images under different names. |
| `mcpAuth.tag` / `mcpGw.tag`                       | `""` (the chart's `appVersion`) | **Do not override** — upgrade the chart version to pick up new images. |
| `mcpAuth.port` / `mcpGw.port`                     | `8080`  | Container/Service port. |
| `mcpAuth.resources` / `mcpGw.resources`           | `mcp-auth`: 200m CPU / 256Mi req, 512Mi limit; `mcp-gw`: 200m CPU / 512Mi req, 1Gi limit | Per-component resources. |
| `service.type`                                    | `ClusterIP` | Service type for both components. |
| `autoscaling.mcpAuth` / `autoscaling.mcpGw`       | `enabled: false`, 1–100 replicas @ 80% CPU | Per-component HPA. When enabled, the Deployment's `replicas` is omitted so the HPA manages it. |
| `serviceAccount.create` / `serviceAccount.name`   | `true` / `""` | Set `create: false` + `name` to reuse an existing SA. |
| `nodeSelector`, `tolerations`, `affinity`, `podAnnotations`, `podLabels`, `podSecurityContext`, `securityContext` | `{}` / `[]` | Applied to **both** deployments. |
| `imagePullSecrets`                                | `[]`    | Pull secret for Docker Hub — see [Registry access](#registry-access). Not needed for ECR on EKS. |
| `volumes`, `volumeMounts`                         | `[]`    | Standard pod-level options. |

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

### Versioning

Chart versions follow [Semantic Versioning](https://semver.org). The chart's `appVersion`
is the tag of the images it ships.

- **Major** — you must change something, or should review a behavior change: a removed or
  renamed setting, a new route, new required network access, higher resource requests, or a
  changed security or access default.
- **Minor** — new images and optional features; no changes required on your side.
- **Patch** — chart or documentation fixes on the same images.

### Upgrading to 2.0.0

Images moved from Frontegg's internal registry to the `fronteggcustomers` Docker Hub
organization, and pulling now requires a credential:

1. Obtain a pull token from Frontegg.
2. Create the `frontegg-registry` pull secret and set `imagePullSecrets` as described in
   [Registry access](#registry-access).
3. Remove any `mcpAuth.repository` / `mcpGw.repository` override that points at
   `527305576865.dkr.ecr.us-east-1.amazonaws.com`.

This release also ships image `7719250`, which changes how the gateway authenticates and is
configured:

- **`fronteggMcpGwHost` is your Frontegg cloud MCP gateway host**, not the host this chart is
  served on. The gateway reads your signing keys and feature flags from it. Set `hybridAuthHost`
  to the public URL clients use, and make your router pass that host through as `Host`.
- **`externalAuthorizationUrl` is deprecated.** The authorization server is
  `https://<fronteggMcpGwHost>`. You can remove it once `fronteggMcpGwHost` is set.
- **Startup checks.** Pods exit at startup when `fronteggMcpGwHost` (or the deprecated
  `externalAuthorizationUrl`) is missing. A missing `hybridAuthHost` is logged as an error.
- **Tenant and user access tokens are rejected** with 401. User tokens and machine tokens are
  unaffected.
- **Requests carry the token's real claims** (tenant, user, application, session). Data the
  gateway keyed by tenant in your Redis resets once: approved policy bypasses (users approve
  again), rate-limit counters and the user-groups cache.
- **Tokens are checked against `applicationId`.** A token issued for another application is
  rejected when `applicationId` is set.
- **`hybridCacheMaxStalenessSeconds: "0"`** now caches signing keys for an hour, as other
  control-plane data, instead of fetching them on every request.
- **Integration tool results are compact JSON** instead of pretty-printed JSON.
- **MCP clients that send no OAuth scope now sign in.** The gateway requests
  `openid profile email` for them.

# MessagePit Email Chart Design

## Goal

Deploy stock MessagePit in Frontegg Kubernetes clusters as a private SendGrid-compatible email sink for Identity and E2E tests. Twilio traffic remains unchanged and continues to use the real provider.

## Scope

The default release contains one MessagePit container in one Kubernetes Deployment with one replica. A ClusterIP Service exposes the SendGrid API on port `8100` and the inbox UI/API on port `8025`. The chart does not create an Ingress, persistent volume, or Twilio adapter image.

The pod is sidecar-ready. Generic `sidecars`, `extraVolumes`, and `service.extraPorts` extension points allow an adapter to be added through values without editing chart templates. A disabled-by-default `messagepit.twilioIngest` switch makes MessagePit listen on pod-local loopback when an adapter is present. The adapter and MessagePit share the pod network namespace, so the internal ingest endpoint is `http://127.0.0.1:8200` and is never routed directly by the Service.

## Runtime configuration

The chart pins `ghcr.io/coreydaley/messagepit:1.3.0` by its multi-architecture manifest digest. MessagePit listens on `0.0.0.0:8100` for SendGrid and `0.0.0.0:8025` for the inbox UI/API. Twilio, webhook capture, and POP3 listeners are disabled through command arguments by default. When `messagepit.twilioIngest.enabled=true`, only the Twilio listener changes: it binds to `127.0.0.1` on the configured internal port for a same-pod adapter. MessagePit's SMTP listener cannot be disabled in this release, so it remains bound inside the pod but is neither declared as a container port nor exposed by the Service.

Storage uses MessagePit's temporary SQLite database on a bounded pod-local `emptyDir` mounted at `/tmp`. `MP_MAX_AGE` defaults to `24h` and `MP_MAX_MESSAGES` defaults to `10000` to bound mailbox growth while covering long E2E runs. Replacing the pod clears this ephemeral database.

## Authentication and secrets

The SendGrid API key and UI basic-auth credentials are Kubernetes Secret values. By default, the chart creates an opaque Secret from `sendgrid.apiKey` and `ui.auth`. Deployments may instead set `existingSecret` to a Secret containing `MP_SENDGRID_API_KEY` and `MP_UI_AUTH`. The Deployment references those keys individually and never renders them into a ConfigMap.

Both values are required. This prevents a release from accidentally deploying an unauthenticated SendGrid endpoint or management API.

Identity is configured separately with:

```text
SENDGRID_BASE_URL=http://<release>-messagepit.<namespace>.svc.cluster.local:8100
SENDGRID_API_KEY=<same value as MP_SENDGRID_API_KEY>
```

`TWILIO_API_URL` remains unset.

## Kubernetes resources

The chart creates:

- A ServiceAccount, configurable or replaceable with an existing account.
- A single-replica Deployment using rolling updates with a maximum of one pod to avoid split inboxes, plus a bounded `emptyDir` for MessagePit's temporary SQLite file.
- A ClusterIP Service with named `ui` and `sendgrid` ports.
- A Secret unless `existingSecret` is configured.
- An optional NetworkPolicy. When enabled, its ingress peers are supplied by the environment-specific values because Identity and E2E namespace labels differ between clusters.

The Deployment uses the image's `messagepit readyz` command for startup and readiness probes and the UI `/healthz` endpoint for liveness. It supports standard pod labels, annotations, image pull secrets, node selectors, tolerations, affinity, resource overrides, sidecar containers, and extra shared volumes. Extra Service ports can target named ports on a sidecar; the optional NetworkPolicy permits those same target ports.

The default container security context disables privilege escalation, drops all capabilities, uses a read-only root filesystem, and runs as a non-root numeric user. These settings must pass a local stock-image smoke test before completion.

## Data flow

1. Identity sends the normal SendGrid v3 request to the Service's `sendgrid` port.
2. MessagePit validates the bearer key and stores the generated email in memory.
3. E2E workers query the Service's `ui` port using basic authentication and exact-recipient matching.
4. Kubernetes restarts an unhealthy pod. Restarting intentionally clears the inbox in this phase.

## Failure behavior

- Missing chart-managed credentials fail Helm rendering through `required` validation.
- A missing key in an externally managed Secret prevents the pod from starting, making configuration failure visible.
- Readiness remains false until MessagePit's storage layer responds.
- The mailbox prunes messages older than 24 hours or beyond the configured maximum.
- No real email is delivered because SMTP relay and forwarding are not configured.

## Out of scope

- Twilio Programmable Messaging migration.
- Twilio Verify emulation.
- A built or maintained Twilio sidecar adapter image.
- Public ingress to the UI/API.
- Persistent volumes or multi-replica MessagePit.
- Changes to Identity or the E2E inbox client.

## Verification

The chart is verified with render assertions, `helm lint`, `helm template` using chart-managed and external Secrets, Kubernetes dry-run parsing where available, and a local container smoke test using the configured non-root/read-only security posture.

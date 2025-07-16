# Entitlements Agent Helm Chart

A Helm chart for deploying Frontegg's Entitlements Agent with SpiceDB, CockroachDB, SpiceDB Sync, and MCP Server.

## Features

- **SpiceDB**: Authorization engine for fine-grained permissions
- **CockroachDB**: Distributed SQL database backend (supports both manual and operator deployments)
- **SpiceDB Sync**: Synchronization service with Frontegg
- **MCP Server**: Management Control Plane server

## Prerequisites

- Kubernetes 1.18+
- Helm 3.0+

### For CockroachDB Operator Mode (Recommended)

When using the CockroachDB Operator (default), you must install the operator first:

```bash
# Install the CockroachDB Operator CRDs
kubectl apply -f https://raw.githubusercontent.com/cockroachdb/cockroach-operator/v2.18.1/install/crds.yaml

# Install the CockroachDB Operator
kubectl apply -f https://raw.githubusercontent.com/cockroachdb/cockroach-operator/v2.18.1/install/operator.yaml
```

## Installation

### Option 1: Using CockroachDB Operator (Recommended)

1. **Install the CockroachDB Operator** (see prerequisites above)

2. **Install the chart with operator mode (default):**

```bash
helm install my-entitlements-agent ./charts/entitlements-agent \
  --set env.spicedbSync.fronteggClientId="your-client-id" \
  --set env.spicedbSync.fronteggClientSecret="your-client-secret"
```

### Option 2: Using Manual CockroachDB StatefulSet

```bash
helm install my-entitlements-agent ./charts/entitlements-agent \
  --set cockroachdb.operator.enabled=false \
  --set env.spicedbSync.fronteggClientId="your-client-id" \
  --set env.spicedbSync.fronteggClientSecret="your-client-secret"
```

## Configuration

### Key Configuration Options

| Parameter                              | Description                 | Default |
| -------------------------------------- | --------------------------- | ------- |
| `cockroachdb.operator.enabled`         | Use CockroachDB Operator    | `true`  |
| `cockroachdb.operator.tlsEnabled`      | Enable TLS for CockroachDB  | `true`  |
| `cockroachdb.replicaCount`             | Number of CockroachDB nodes | `3`     |
| `spicedb.replicaCount`                 | Number of SpiceDB replicas  | `1`     |
| `env.spicedbSync.fronteggClientId`     | Frontegg Client ID          | `""`    |
| `env.spicedbSync.fronteggClientSecret` | Frontegg Client Secret      | `""`    |

### CockroachDB Operator Configuration

```yaml
cockroachdb:
  operator:
    enabled: true # Use CockroachDB Operator
    tlsEnabled: true # Enable TLS (recommended for production)
    additionalLabels: {} # Additional labels for CrdbCluster
    additionalAnnotations: {} # Additional annotations for CrdbCluster
  replicaCount: 3 # Number of CockroachDB nodes
  persistence:
    size: 20Gi # Storage size per node
    storageClass: "" # Storage class (empty = default)
```

### Manual CockroachDB Configuration

```yaml
cockroachdb:
  operator:
    enabled: false # Disable operator, use manual StatefulSet
  replicaCount: 3 # Number of CockroachDB nodes
  persistence:
    enabled: true # Enable persistent storage
    size: 20Gi # Storage size per node
    storageClass: "" # Storage class (empty = default)
```

### SpiceDB Configuration

```yaml
spicedb:
  repository: authzed/spicedb
  tag: latest
  replicaCount: 1
  logLevel: trace
  grpcPresharedKey: spicedb
```

### Resource Configuration

```yaml
resources:
  spicedb:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      memory: 1Gi
  cockroachdb:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      memory: 2Gi
```

## Deployment Modes Comparison

| Feature              | CockroachDB Operator | Manual StatefulSet    |
| -------------------- | -------------------- | --------------------- |
| **Setup Complexity** | Simple (CRD-based)   | Manual configuration  |
| **TLS Support**      | Built-in             | Manual setup required |
| **Scaling**          | Automatic            | Manual                |
| **Backup**           | Operator-managed     | Manual                |
| **Monitoring**       | Operator-provided    | Manual setup          |
| **Production Ready** | ✅ Recommended       | ⚠️ Requires expertise |

## Accessing Services

### SpiceDB

```bash
# Port-forward to SpiceDB
kubectl port-forward service/my-entitlements-agent-spicedb 50051:50051

# Use zed CLI or SpiceDB client
zed context set my-context my-entitlements-agent-spicedb:50051 spicedb --insecure
```

### CockroachDB

#### With Operator (TLS enabled)

```bash
# Get the client certificate (operator creates these automatically)
kubectl get secret my-entitlements-agent-cockroachdb-client -o yaml

# Connect using client certificate
kubectl run cockroachdb-client --rm -it --image=cockroachdb/cockroach --restart=Never \
  -- sql --certs-dir=/certs --host=my-entitlements-agent-cockroachdb-public
```

#### Manual Mode (insecure)

```bash
# Connect directly (insecure mode)
kubectl run cockroachdb-client --rm -it --image=cockroachdb/cockroach --restart=Never \
  -- sql --insecure --host=my-entitlements-agent-cockroachdb
```

## Troubleshooting

### CockroachDB Operator Issues

1. **Operator not installed:**

   ```bash
   kubectl get crd crdbclusters.crdb.cockroachlabs.com
   ```

2. **Check operator logs:**
   ```bash
   kubectl logs -n cockroach-operator-system deployment/cockroach-operator
   ```

### SpiceDB Issues

1. **Check SpiceDB logs:**

   ```bash
   kubectl logs deployment/my-entitlements-agent-spicedb
   ```

2. **Verify database connection:**
   ```bash
   kubectl exec deployment/my-entitlements-agent-spicedb -- \
     spicedb datastore migrate head --datastore-engine=cockroachdb \
     --datastore-conn-uri="postgres://..."
   ```

### Common Issues

1. **Init jobs failing**: Check if CockroachDB is ready and accessible
2. **SpiceDB not ready**: Verify database migrations completed successfully
3. **Connection refused**: Ensure services are properly configured for your deployment mode

## Upgrading

### From Manual to Operator Mode

1. **Backup your data** (important!)
2. **Install the CockroachDB Operator**
3. **Upgrade with operator enabled:**
   ```bash
   helm upgrade my-entitlements-agent ./charts/entitlements-agent \
     --set cockroachdb.operator.enabled=true \
     --reuse-values
   ```

### Standard Upgrades

```bash
helm upgrade my-entitlements-agent ./charts/entitlements-agent --reuse-values
```

## Uninstallation

```bash
# Uninstall the Helm release
helm uninstall my-entitlements-agent

# If using operator mode, optionally clean up the CockroachDB Operator
kubectl delete -f https://raw.githubusercontent.com/cockroachdb/cockroach-operator/v2.18.1/install/operator.yaml
kubectl delete -f https://raw.githubusercontent.com/cockroachdb/cockroach-operator/v2.18.1/install/crds.yaml
```

## Contributing

For bugs and feature requests, please create an issue in the repository.

## License

This chart is licensed under the same terms as the Frontegg Entitlements Agent.

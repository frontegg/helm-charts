# Frontegg secure-access

![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square)

## Introduction
Helm 3 chart deployment for Frontegg Secure Access experience.  

## Installation (helm 3)
```console
helm repo add frontegg https://frontegg.github.io/helm-charts/
helm repo update
helm upgrade --install <release> frontegg/secure-access ./
```

## Example required configuration 
```yaml
secure-access:

  frontegg:
    images:
      enabled: <true for auto generated image registry secret>
      username: <Frontegg image repository user name, given by frontegg>
      password: <Frontegg image repository password, given by frontegg>

  api-gateway:
    frontegg:
      authenticationPublicKey: <Frontegg authentication public key, given by frontegg>

  team-management-service:
    database:
      host: <Local Mysql host name>
      userName: <Local Mysql user name>
      password: <Local Mysql password>
    redis:
      host: <Local Redis host name>
      password: <Local Redis password>
      tls: <Local Redis tls support (true|fasle)>
    saml:
      publicKey: <SAML public key, provided by Frontegg>
      privateKey: <SAML private key, provided by Frontegg>
      certificate: <SAML certificate, provided by Frontegg>
    frontegg:
      clientId: <clientId, provided by Frontegg > # ref:https://portal.frontegg.com/administration

  identity-service:
    database:
      host: <Local Mysql host name>
      userName: <Local Mysql user name>
      password: <Local Mysql password>
    redis:
      host: <Local Redis host name>
      password: <Local Redis password>
      tls: <Local Redis tls support (true|fasle)>
    email:
      apiKey: <Email Api Key, provided by Frontegg>
    frontegg:
      clientId: <clientId, provided by Frontegg > # ref:https://portal.frontegg.com/administration
      apiKey: <Api key, provided by Frontegg > # ref:https://portal.frontegg.com/administration
      sync:
        enabled: <true for hybrid, use false for airGap>
```

with detailed comments, visit the chart's [values.yaml](https://github.com/frontegg/helm-charts/blob/master/charts/secure-access/values.yaml), or run these configuration commands:

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| api-gateway.affinity | object | `{}` | Provide deployment affinity |
| api-gateway.appVersion | string | `"latest"` | Provide the image docker tag default: latest |
| api-gateway.autoscaling | object | `{"enabled":true,"maxReplicas":4,"minReplicas":2,"targetCPUUtilizationPercentage":75,"targetMemoryUtilizationPercentage":75}` | HPA properties for team-management-service -- If autoscaling is enabled it will monitor the service and raise or lower pods amount based upon usage -- If autoscaling is disabled team-management-service will be managed by replicaset with `replicaCount` determine pod amount |
| api-gateway.configuration.map | object | `{}` |  |
| api-gateway.configuration.secrets | object | `{}` |  |
| api-gateway.frontegg.apiGatewayUrl | string | `"https://api.frontegg.com"` |  |
| api-gateway.frontegg.authenticationPublicKey | string | `""` |  |
| api-gateway.frontegg.authenticationServiceUrl | string | `"https://api.frontegg.com/auth/vendor"` |  |
| api-gateway.frontegg.hybridServices | string | `"identity,team"` |  |
| api-gateway.frontegg.metadataServiceUrl | string | `"https://api.frontegg.com/metadata"` |  |
| api-gateway.fullnameOverride | string | `""` | Provide a name instead of {releaseName}-api-gateway |
| api-gateway.image | object | `{"pullPolicy":"Always","repository":"frontegg/hybrid-api-gateway"}` | Manage docker image properties |
| api-gateway.image.pullPolicy | string | `"Always"` | Provide image pull policy |
| api-gateway.image.repository | string | `"frontegg/hybrid-api-gateway"` | Provide docker image repository |
| api-gateway.imagePullSecrets | list | `[{"name":"regcred"}]` | Provide secret name for Frontegg's docker image repository. |
| api-gateway.ingress | object | `{"annotations":{},"enabled":false,"hostnameOverride":"","tls":{"enabled":false,"secretName":""}}` | Enable Ingress if access from the internet is needed |
| api-gateway.ingress.annotations | object | `{}` | provide the needed ingress annotation -- example: --  kubernetes.io/tls-acme: "true" --  kubernetes.io/ingress.class: "nginx" --  ingress.kubernetes.io/force-ssl-redirect: "true" --  nginx.ingress.kubernetes.io/server-snippet: | --    location ~* ^/(metrics|healthcheck) { --      deny all; --      return 403; --    } |
| api-gateway.ingress.tls | object | `{"enabled":false,"secretName":""}` | If enabled ingress will search for secret to enable TLS |
| api-gateway.nameOverride | string | `""` | override application name instead of api-gateway for `app:` labels |
| api-gateway.network | object | `{"adminsServiceUrl":"http://frontegg-admins-service","auditsServiceUrl":"http://frontegg-audits-service","authenticationServiceUrl":"http://frontegg-authentication-service","eventsServiceUrl":"http://frontegg-event-service","featureFlagsServiceUrl":"http://frontegg-feature-flags-service","identityServiceUrl":"http://frontegg-identity-service","integrationsServiceUrl":"http://frontegg-integrations-service","metadataServiceUrl":"http://frontegg-metadata-service","notificationServiceUrl":"http://frontegg-notification-service","reportsEngineUrl":"http://frontegg-reporting-engine","reportsServiceUrl":"http://frontegg-reporting-service","teamServiceUrl":"http://frontegg-team-management-service","tenantsServiceUrl":"http://frontegg-tenants-service","vendorsServiceUrl":"http://frontegg-vendors-service","webhookServiceUrl":"http://frontegg-webhook-service","webpushServiceUrl":"http://frontegg-webpush-service"}` | Frontegg's services url for inner communications -- Provide an alternate url for a service if a service name was changed |
| api-gateway.nodeSelector."beta.kubernetes.io/os" | string | `"linux"` |  |
| api-gateway.replicaCount | int | `2` | Provide the amount of pods if HPA is not enabled |
| api-gateway.resources | object | `{"limits":{"cpu":"250m","memory":"512Mi"},"requests":{"cpu":"250m","memory":"512Mi"}}` | Set api-gateway resources |
| api-gateway.service.name | string | `"access-port"` |  |
| api-gateway.service.port | int | `80` |  |
| api-gateway.service.protocol | string | `"TCP"` | Set service port |
| api-gateway.service.targetPort | int | `9090` | Set port protocol default: TCP |
| api-gateway.service.type | string | `"ClusterIP"` | Set service type |
| api-gateway.tolerations | list | `[]` | Provide deployment tolerations |
| frontegg | object | `{"images":{"enabled":true,"password":"","registry":"docker.io","username":""}}` | Set frontegg's configurations |
| frontegg.images | object | `{"enabled":true,"password":"","registry":"docker.io","username":""}` | Docker Images registry properties |
| frontegg.images.enabled | bool | `true` | Set enabled to create a secret with Frontegg's registry properties |
| frontegg.images.password | string | `""` | Set password for docker registry provided by Frontegg |
| frontegg.images.registry | string | `"docker.io"` | Set registry name |
| frontegg.images.username | string | `""` | Set username for docker registry provided by Frontegg |
| identity-service.affinity | object | `{}` | Provide deployment affinity |
| identity-service.appVersion | string | `"latest"` | Provide the image docker tag default: latest |
| identity-service.autoscaling | object | `{"enabled":true,"maxReplicas":4,"minReplicas":2,"targetCPUUtilizationPercentage":75,"targetMemoryUtilizationPercentage":75}` | HPA properties for identity-service -- If autoscaling is enabled it will monitor the service and raise or lower pods amount based upon usage -- If autoscaling is disabled identity-service will be managed by replicaset with `replicaCount` determine pod amount |
| identity-service.configuration.map | object | `{}` |  |
| identity-service.configuration.secrets | object | `{}` |  |
| identity-service.database | object | `{"host":"","name":"frontegg_identity","password":"","ssl":"true","username":""}` | Set database connection string values |
| identity-service.email | object | `{"apiKey":""}` | Set frontegg's api key for emails |
| identity-service.frontegg | object | `{"apiKey":"","authenticationUrl":"https://api.frontegg.com/vendors/auth/token","clientId":"","managedIdentityServiceUrl":"https://api.frontegg.com/identity","sync":{"authenticationRetryDelay":"5000","enabled":"true","intervalTime":"15","shutdownOnAuthenticationFailure":"true"}}` | Set Frontegg's api key for emails |
| identity-service.frontegg.authenticationUrl | string | `"https://api.frontegg.com/vendors/auth/token"` | Set Frontegg's Authentication Url |
| identity-service.frontegg.clientId | string | `""` | Set Frontegg provided in frontegg's portal administration |
| identity-service.frontegg.managedIdentityServiceUrl | string | `"https://api.frontegg.com/identity"` | Set Frontegg's identity service url |
| identity-service.frontegg.sync.authenticationRetryDelay | string | `"5000"` | Set authentication failure retry delay in milliseconds. |
| identity-service.frontegg.sync.enabled | string | `"true"` | Enable Configuration sync process with Frontegg's managed cloud |
| identity-service.frontegg.sync.intervalTime | string | `"15"` | Set sync time interval (minutes) with Frontegg's managed cloud. |
| identity-service.frontegg.sync.shutdownOnAuthenticationFailure | string | `"true"` | Set true to shutdown secure access in case of authentication failure on pod startup. |
| identity-service.fullnameOverride | string | `""` | Provide a name in place of {releaseName}-identity-service |
| identity-service.image | object | `{"pullPolicy":"Always","repository":"frontegg/hybrid-identity-service"}` | Manage docker image properties |
| identity-service.image.pullPolicy | string | `"Always"` | Provide image pull policy |
| identity-service.image.repository | string | `"frontegg/hybrid-identity-service"` | Provide docker repository hub |
| identity-service.imagePullSecrets | list | `[{"name":"regcred"}]` | Provide secret name for frontegg's repository |
| identity-service.nameOverride | string | `""` | Provide a name in place of identity-service for `app:` labels |
| identity-service.network | object | `{"teamServiceUrl":"http://frontegg-team-management-service"}` | Frontegg's services url for inner communications -- Provide an alternate url for a service if a service name was changed |
| identity-service.nodeSelector."beta.kubernetes.io/os" | string | `"linux"` |  |
| identity-service.podAnnotations | object | `{}` |  |
| identity-service.podSecurityContext | object | `{}` |  |
| identity-service.redis | object | `{"host":"","password":"","port":"6379","tls":"true"}` | Set Redis connection string values |
| identity-service.replicaCount | int | `2` | Provide the amount of pods if HPA is not enabled |
| identity-service.resources | object | `{"limits":{"cpu":"250m","memory":"512Mi"},"requests":{"cpu":"250m","memory":"512Mi"}}` | Set identity-service resources |
| identity-service.service | object | `{"name":"access-port","port":80,"protocol":"TCP","targetPort":3016,"type":"ClusterIP"}` | Setup Service properties for identity-service (open only one port) |
| identity-service.service.name | string | `"access-port"` | Set port name |
| identity-service.service.port | int | `80` | Set service target port to map |
| identity-service.service.protocol | string | `"TCP"` | Set service port |
| identity-service.service.targetPort | int | `3016` | Set port protocol default: TCP |
| identity-service.service.type | string | `"ClusterIP"` | Set service type |
| identity-service.tolerations | list | `[]` | Provide deployment tolerations |
| team-management-service.affinity | object | `{}` | Provide deployment affinity |
| team-management-service.appVersion | string | `"latest"` | Provide the image docker tag default: latest |
| team-management-service.autoscaling | object | `{"enabled":true,"maxReplicas":3,"minReplicas":2,"targetCPUUtilizationPercentage":75,"targetMemoryUtilizationPercentage":75}` | HPA properties for team-management-service -- If autoscaling is enabled it will monitor the service and raise or lower pods amount based upon usage -- If autoscaling is disabled team-management-service will be managed by replicaset with `replicaCount` determine pod amount |
| team-management-service.cloudEnvironment | string | `"prod"` | Set could environment managed by team-management-service -- Possible values (prod | dev) |
| team-management-service.configuration.map | object | `{}` |  |
| team-management-service.configuration.secret | object | `{}` |  |
| team-management-service.database | object | `{"host":"","name":"frontegg_team_management","password":"","ssl":"true","userName":""}` | Set database connection string values |
| team-management-service.frontegg | object | `{"clientId":""}` | Set frontegg properties |
| team-management-service.fullnameOverride | string | `""` | Provide a name in place of {releaseName}-team-management-service |
| team-management-service.image | object | `{"pullPolicy":"Always","repository":"frontegg/hybrid-team-management-service"}` | Manage docker image properties |
| team-management-service.image.pullPolicy | string | `"Always"` | Provide image pull policy |
| team-management-service.image.repository | string | `"frontegg/hybrid-team-management-service"` | Provide docker repository hub |
| team-management-service.imagePullSecrets | list | `[{"name":"regcred"}]` | Provide secret name for frontegg's repository |
| team-management-service.nameOverride | string | `""` | Provide a name in place of team-management-service for `app:` labels |
| team-management-service.network | object | `{"adminsServiceUrl":"http://frontegg-admins-service","auditsServiceUrl":"http://frontegg-audits-service","authenticationServiceUrl":"http://frontegg-authentication-service","eventsServiceUrl":"http://frontegg-event-service","featureFlagsServiceUrl":"http://frontegg-feature-flags-service","identityServiceUrl":"http://frontegg-identity-service","integrationsServiceUrl":"http://frontegg-integrations-service","metadataServiceUrl":"http://frontegg-metadata-service","notificationServiceUrl":"http://frontegg-notification-service","reportsEngineUrl":"http://frontegg-reporting-engine","reportsServiceUrl":"http://frontegg-reporting-service","teamServiceUrl":"http://frontegg-team-management-service","tenantsServiceUrl":"http://frontegg-tenants-service","vendorsServiceUrl":"http://frontegg-vendors-service","webhookServiceUrl":"http://frontegg-webhook-service","webpushServiceUrl":"http://frontegg-webpush-service"}` | Frontegg's services url for inner communications -- Provide an alternate url for a service if a service name was changed |
| team-management-service.nodeSelector."beta.kubernetes.io/os" | string | `"linux"` |  |
| team-management-service.redis | object | `{"host":"","index":"1","password":"","port":"6379","tls":"true"}` | Set Redis connection string values |
| team-management-service.replicaCount | int | `2` | Provide the amount of pods if HPA is not enabled |
| team-management-service.resources.limits.cpu | string | `"250m"` |  |
| team-management-service.resources.limits.memory | string | `"512Mi"` |  |
| team-management-service.resources.requests.cpu | string | `"250m"` |  |
| team-management-service.resources.requests.memory | string | `"512Mi"` |  |
| team-management-service.saml | object | `{"certificate":"","privateKey":"","publicKey":""}` | Set saml properties, values should be provided by Frontegg. |
| team-management-service.service | object | `{"name":"http","port":80,"protocol":"TCP","targetPort":3003,"type":"ClusterIP"}` | Setup Service properties for team-management-service (open only one port) |
| team-management-service.service.name | string | `"http"` | Set port name |
| team-management-service.service.port | int | `80` | Set service port |
| team-management-service.service.protocol | string | `"TCP"` | Set port protocol default: TCP |
| team-management-service.service.targetPort | int | `3003` | Set service target port to map |
| team-management-service.service.type | string | `"ClusterIP"` | Set service type |
| team-management-service.tolerations | list | `[]` | Provide deployment tolerations |

----------------------------------------------

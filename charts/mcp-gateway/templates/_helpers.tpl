{{/*
Expand the name of the chart.
*/}}
{{- define "name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 47 chars to leave room for suffixes like -auth, -gw, -test-connection (up to 16 chars).
This ensures the final resource name stays within Kubernetes' 63-character DNS label limit.
If release name contains chart name it will be used as a full name.
*/}}
{{- define "fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 47 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 47 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 47 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "chartName" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "commonLabels" -}}
helm.sh/chart: {{ include "chartName" . }}
{{ include "selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "selectorLabels" -}}
app.kubernetes.io/name: {{ include "name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Container image for a component: its `repository` when set, otherwise
<imageRegistry>/<image name>, tagged with its `tag` or the chart's appVersion.
Usage: include "componentImage" (dict "root" . "component" .Values.mcpGw "name" "hybrid-agen-co-gw")
*/}}
{{- define "componentImage" -}}
{{- $registry := required "imageRegistry is required" .root.Values.imageRegistry | trimSuffix "/" -}}
{{- $repository := .component.repository | default (printf "%s/%s" $registry .name) -}}
{{- printf "%s:%s" $repository (.component.tag | default .root.Chart.AppVersion) -}}
{{- end }}

{{/*
Convert camelCase to UPPER_SNAKE_CASE
*/}}
{{- define "toEnvVarName" -}}
{{- $result := regexReplaceAll "([a-z0-9])([A-Z])" . "${1}_${2}" -}}
{{- $result | upper -}}
{{- end }}

{{/*
envFrom block loading a pre-existing Secret (.Values.existingSecret) into the
container. Renders nothing when unset.
*/}}
{{- define "secretEnvFrom" -}}
{{- with .Values.existingSecret -}}
envFrom:
  - secretRef:
      name: {{ . }}
{{- end -}}
{{- end -}}

{{/* Expand the chart name. */}}
{{- define "messagepit.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Create a default fully qualified application name. */}}
{{- define "messagepit.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/* Create chart name and version as used by the chart label. */}}
{{- define "messagepit.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Common labels. */}}
{{- define "messagepit.labels" -}}
helm.sh/chart: {{ include "messagepit.chart" . }}
{{ include "messagepit.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/* Selector labels. */}}
{{- define "messagepit.selectorLabels" -}}
app.kubernetes.io/name: {{ include "messagepit.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/* ServiceAccount name. */}}
{{- define "messagepit.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "messagepit.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/* Credential Secret name. */}}
{{- define "messagepit.secretName" -}}
{{- if .Values.existingSecret }}
{{- .Values.existingSecret }}
{{- else if and .Values.externalSecret.enabled .Values.externalSecret.targetSecretName }}
{{- .Values.externalSecret.targetSecretName }}
{{- else }}
{{- include "messagepit.fullname" . }}
{{- end }}
{{- end }}

{{/* Public inbox hostname. */}}
{{- define "messagepit.ingressHostname" -}}
{{- if .Values.ingress.hostname }}
{{- .Values.ingress.hostname }}
{{- else }}
{{- $subdomain := required "venvSubDomain is required when ingress.hostname is empty" .Values.venvSubDomain }}
{{- $domain := required "venvDomain is required when ingress.hostname is empty" .Values.venvDomain }}
{{- printf "messagepit.%s.%s" $subdomain $domain }}
{{- end }}
{{- end }}

{{/* Reject ambiguous credential ownership. */}}
{{- define "messagepit.validateCredentials" -}}
{{- if and .Values.externalSecret.enabled .Values.existingSecret }}
{{- fail "externalSecret.enabled and existingSecret are mutually exclusive" }}
{{- end }}
{{- end }}

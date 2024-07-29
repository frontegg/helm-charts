{{/* Hostname is used in services who render ingress */}}
{{- define "unified.hostname" -}}
{{- required "I need to know the host: .Values.ingress.hostnameOverride is required when ingress enabled" .Values.ingress.hostnameOverride | trimSuffix "-" }}
{{- end -}}

{{/* Just the name */}}
{{- define "name" -}}
{{- required "I cant live without a name: .Values.name must be set" .Values.name }}{{ include "unified.suffix" . }}
{{- end -}}

{{/* calculate the suffix */}}
{{- define "unified.suffix" -}}
{{- with .Values.nameSuffix -}}
-{{ . | trunc 10 }}
{{- end -}}
{{- end -}}

{{/* kubernetes web service name */}}
{{- define "web.name" -}}
{{ include "name" . }}-web
{{- end -}}

{{/* kubernetes worker service name */}}
{{- define "worker.name" -}}
{{ include "name" . }}-worker
{{- end -}}

{{/* kubernetes high priority service name */}}
{{- define "hp.name" -}}
{{ include "name" . }}-hp
{{- end -}}

{{/* Some services include fullname in their values */}}
{{- define "fullname" -}}
{{ include "name" . }}
{{- end -}}

{{/* Create chart name and version as used by the chart label. */}}
{{- define "unified.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* inject env variables directly */}}
{{- define "container.env" -}}
{{- range $envVar := .env }}
- name: {{ required "envVar.name required" $envVar.name | quote }}
  value: {{ required "envVar.value required" $envVar.value | quote }}
{{- end }}
{{- end -}}

{{- define "externalsecret.volumemount" -}}
- name: vol-secret
  mountPath: {{ .Values.externalSecret.mountPath }}
  subPath: {{ .Values.externalSecret.subPath }} 
{{- end -}}

{{/* Common labels includes selectorLabels */}}
{{- define "labels" -}}
helm.sh/chart: {{ include "unified.chart" . }}
app.frontegg.com/team: {{ required "Every service needs to have responsible parents. .Values.team is required." .Values.team }}
{{- with .Values.web.labels }}
{{ toYaml . }}
{{- end }}
{{ include "selectorLabels" . }}
app.frontegg.io/version: {{ .Chart.Version | quote }}
app.frontegg.io/managed-by: {{ .Release.Service }}
app.frontegg.com/appVersion: {{ include "appVersion" . }}
{{- end -}}

{{/* Selector labels */}}
{{- define "selectorLabels" -}}
app.frontegg.com/name: {{ include "name" . }}
app.frontegg.com/instance: {{ .Release.Name }}
{{- end -}}

{{- define "jobLabels" -}}
app.frontegg.com/name: {{ include "name" . }}-job
app.frontegg.com/instance: {{ .Release.Name }}
{{- end -}}

{{- define "cronJobLabels" -}}
app.frontegg.com/name: {{ include "name" . }}-cronjob
app.frontegg.com/instance: {{ .Release.Name }}
{{- end -}}

{{- define "workerLabels" -}}
app.frontegg.com/team: {{ required ".Values.team is required" .Values.team }}
app.frontegg.com/appVersion: {{ include "appVersion" . }}
{{- with .Values.worker.labels }}
{{ toYaml . }}
{{- end }}
{{ include "workerSelectorLabels" . }}
{{- end -}}

{{- define "workerSelectorLabels" -}}
app.frontegg.com/name: {{ include "name" . }}-worker
{{- end -}}

{{- define "appVersion" -}}
{{ required "NEED APPVERSION: .Values.appVersion is required cant run without it" .Values.appVersion }}
{{- end -}}

{{- define "name-app-version" -}}
{{ include "name" . }}-{{ include "appVersion" . }}
{{- end -}}

{{/*
Common labels includes HP selectorLabels
*/}}
{{- define "hp.labels" -}}
app.frontegg.com/team: {{ .Values.team }}
helm.sh/chart: {{ include "unified.chart" . }}
app.frontegg.io/version: {{ .Chart.Version | quote }}
app.frontegg.io/managed-by: {{ .Release.Service }}
app.frontegg.com/appVersion: {{ include "appVersion" . }}
{{ include "hp.selectorLabels" . }}
{{- end -}}

{{/*
Selector labels for high priority pods
*/}}
{{- define "hp.selectorLabels" -}}
app.frontegg.com/name: {{ include "name" . }}-hp
app.frontegg.com/instance: {{ .Release.Name }}
{{- end -}}


{{- define "keda.annotations" -}}
{{- .Values.keda.annotations | toYaml }}
{{- end -}}
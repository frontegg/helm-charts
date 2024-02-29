{{/* Hostname is used in services who render ingress */}}
{{- define "unified.hostname" -}}
{{- required ".Values.ingress.hostnameOverride is required when ingress enabled" .Values.ingress.hostnameOverride | trimSuffix "-" }}
{{- end -}}

{{/* Just the name */}}
{{- define "unified.name" -}}
{{- required ".Values.name must be set" .Values.name }}{{ include "unified.suffix" . }}
{{- end -}}

{{/* calculate the suffix */}}
{{- define "unified.suffix" -}}
{{- with .Values.nameSuffix -}}
-{{ . | trunc 10 }}
{{- end -}}
{{- end -}}

{{/* kubernetes web service name */}}
{{- define "unified.web.svc.name" -}}
{{ include "unified.name" . }}-web
{{- end -}}

{{/* kubernetes worker service name */}}
{{- define "unified.worker.svc.name" -}}
{{ include "unified.name" . }}-worker
{{- end -}}

{{/* kubernetes high priority service name */}}
{{- define "unified.hp.svc.name" -}}
{{ include "unified.name" . }}-hp
{{- end -}}

{{/* Some services include fullname in their values */}}
{{- define "fullname" -}}
{{ include "unified.name" . }}
{{- end -}}

{{/* Create chart name and version as used by the chart label. */}}
{{- define "unified.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* inject env variables directly */}}
{{- define "unified.container.env" -}}
{{- range $envVar := .env -}}
- name: {{ required "envVar.name required" $envVar.name | quote }}
  value: {{ required "envVar.value required" $envVar.value | quote }}
{{- end -}}
{{- end -}}

{{- define "unified.externalsecret.volumemount" -}}
- name: vol-secret
  mountPath: {{ .Values.externalSecret.mountPath }}
  subPath: {{ .Values.externalSecret.subPath }} 
{{- end -}}

{{/* Common labels includes selectorLabels */}}
{{- define "unified.labels" -}}
helm.sh/chart: {{ include "unified.chart" . }}
app.frontegg.com/team: {{ .Values.team }}
{{- with .Values.web.labels }}
{{ toYaml . }}
{{- end }}
{{ include "unified.selectorLabels" . }}
app.frontegg.io/version: {{ .Chart.Version | quote }}
app.frontegg.io/managed-by: {{ .Release.Service }}
app.frontegg.com/appVersion: {{ .Values.appVersion | quote }}
{{- end -}}

{{/* Selector labels */}}
{{- define "unified.selectorLabels" -}}
app.frontegg.com/name: {{ include "unified.name" . }}
app.frontegg.com/instance: {{ .Release.Name }}
{{- end -}}

{{- define "unified.jobLabels" -}}
app.frontegg.com/name: {{ include "unified.name" . }}-job
app.frontegg.com/instance: {{ .Release.Name }}
{{- end -}}

{{- define "unified.cronJobLabels" -}}
app.frontegg.com/name: {{ include "unified.name" . }}-cronjob
app.frontegg.com/instance: {{ .Release.Name }}
{{- end -}}

{{- define "unified.workerLabels" -}}
app.frontegg.com/team: {{ required ".Values.team is required" .Values.team }}
app.frontegg.com/appVersion: {{ .Values.appVersion | quote }}
{{- with .Values.worker.labels }}
{{ toYaml . }}
{{- end }}
{{ include "unified.workerSelectorLabels" . }}
{{- end -}}

{{- define "unified.workerSelectorLabels" -}}
app.frontegg.com/name: {{ include "unified.name" . }}-worker
{{- end -}}

{{- define "external-secret-unique-name" -}}
{{ include "unified.name" . }}-secret-{{ now | unixEpoch }}
{{- end -}}

{{- define "isLinkerdInjectEnabled" -}}
{{- if and .podAnnotations (eq (index .podAnnotations "linkerd.io/inject") "enabled") -}}
  true
{{- else -}}
  false
{{- end -}}
{{- end -}}

{{/*
Common labels includes HP selectorLabels
*/}}
{{- define "unified.hp.labels" -}}
app.frontegg.com/team: {{ .Values.team }}
helm.sh/chart: {{ include "unified.chart" . }}
app.frontegg.io/version: {{ .Chart.Version | quote }}
app.frontegg.io/managed-by: {{ .Release.Service }}
app.frontegg.com/appVersion: {{ .Values.appVersion | quote }}
{{ include "unified.hp.selectorLabels" . }}
{{- end -}}

{{/*
Selector labels for high priority pods
*/}}
{{- define "unified.hp.selectorLabels" -}}
app.frontegg.com/name: {{ include "unified.name" . }}-hp
app.frontegg.com/instance: {{ .Release.Name }}
{{- end -}}

{{/* Hostname is used in services who render ingress */}}
{{- define "fuc.hostname" -}}
{{- if .Values.ingress.hostnameOverride -}}
{{- .Values.ingress.hostnameOverride | trimSuffix "-" -}}
{{- else -}}
{{- printf "api-%s.dev.frontegg.com" .Release.Name | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/* Just the serviceName */}}
{{- define "fuc.name" -}}
{{- required ".Values.serviceName must be set" .Values.serviceName }}-v2
{{- end -}}

{{/* kubernetes web service name */}}
{{- define "fuc.web.svc.name" -}}
{{ include "fuc.name" . }}-web
{{- end -}}

{{/* kubernetes worker service name */}}
{{- define "fuc.worker.svc.name" -}}
{{ include "fuc.name" . }}-worker
{{- end -}}

{{/* kubernetes high priority service name */}}
{{- define "fuc.hp.svc.name" -}}
{{ include "fuc.name" . }}-hp
{{- end -}}

{{/* Some services include fullname in their values */}}
{{- define "fullname" -}}
{{ include "fuc.name" . }}
{{- end -}}

{{/* Create chart name and version as used by the chart label. */}}
{{- define "fuc.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Common labels includes selectorLabels */}}
{{- define "fuc.labels" -}}
helm.sh/chart: {{ include "fuc.chart" . }}
app.frontegg.com/team: {{ .Values.team }}
{{ include "fuc.selectorLabels" . }}
app.frontegg.io/version: {{ .Chart.Version | quote }}
app.frontegg.io/managed-by: {{ .Release.Service }}
app.frontegg.com/appVersion: {{ .Values.appVersion | quote }}
{{- end -}}

{{/* Selector labels */}}
{{- define "fuc.selectorLabels" -}}
app.frontegg.com/name: {{ include "fuc.name" . }}
app.frontegg.com/instance: {{ .Release.Name }}
{{- end -}}

{{- define "fuc.jobLabels" -}}
app.frontegg.com/name: {{ include "fuc.name" . }}-job
app.frontegg.com/instance: {{ .Release.Name }}
{{- end -}}


{{- define "fuc.workerLabels" -}}
app.frontegg.com/team: {{ required ".Values.team is required" .Values.team }}
app.frontegg.com/appVersion: {{ .Values.appVersion | quote }}
{{ include "fuc.workerSelectorLabels" . }}
{{- end -}}

{{- define "fuc.workerSelectorLabels" -}}
app.frontegg.com/name: {{ include "fuc.name" . }}-worker
{{- end -}}

{{- define "external-secret-unique-name" -}}
{{ include "fuc.name" . }}-secret-{{ now | unixEpoch }}
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
{{- define "fuc.hp.labels" -}}
app.frontegg.com/team: {{ .Values.team }}
helm.sh/chart: {{ include "fuc.chart" . }}
app.frontegg.io/version: {{ .Chart.Version | quote }}
app.frontegg.io/managed-by: {{ .Release.Service }}
app.frontegg.com/appVersion: {{ .Values.appVersion | quote }}
{{ include "fuc.hp.selectorLabels" . }}
{{- end -}}

{{/*
Selector labels for high priority pods
*/}}
{{- define "fuc.hp.selectorLabels" -}}
app.frontegg.com/name: {{ include "fuc.name" . }}-hp
app.frontegg.com/instance: {{ .Release.Name }}
{{- end -}}

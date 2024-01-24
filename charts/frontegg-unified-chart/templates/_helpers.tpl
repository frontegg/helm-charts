{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "fuc.hostname" -}}
{{- if .Values.ingress.hostnameOverride -}}
{{- .Values.ingress.hostnameOverride | trimSuffix "-" -}}
{{- else -}}
{{- printf "api-%s.dev.frontegg.com" .Release.Name | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "fuc.name" -}}
{{- required ".Values.serviceName must be set" .Values.serviceName | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Some services include fullname in their values
*/}}
{{- define "fullname" -}}
{{ include "fuc.name" . }}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "fuc.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels includes selectorLabels
*/}}
{{- define "fuc.labels" -}}
helm.sh/chart: {{ include "fuc.chart" . }}
app.frontegg.com/team: {{ .Values.team }}
{{ include "fuc.selectorLabels" . }}
app.frontegg.io/version: {{ .Chart.Version | quote }}
app.frontegg.io/managed-by: {{ .Release.Service }}
app.frontegg.com/appVersion: {{ .Values.appVersion | quote }}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "fuc.selectorLabels" -}}
app.frontegg.com/name: {{ include "fuc.name" . }}
app.frontegg.com/instance: {{ .Release.Name }}
{{- end -}}

{{- define "fuc.jobLabels" -}}
app.frontegg.com/name: {{ include "fuc.name" . }}-job
app.frontegg.com/instance: {{ .Release.Name }}
{{- end -}}


{{- define "fuc.workerLabels" -}}
app.frontegg.com/team: {{ .Values.team }}
app.frontegg.com/name: {{ include "fuc.name" . }}-worker
app.frontegg.com/appVersion: {{ .Values.appVersion | quote }}
{{- end -}}

{{- define "fuc.workerSelectorLabels" -}}
app.frontegg.com/name: {{ include "fuc.name" . }}-worker
{{- end -}}

{{- define "external-secret-unique-name" -}}
{{ include "fuc.name" . }}-external-secret-{{ now | unixEpoch }}
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

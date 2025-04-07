{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}

{{/*
Expand the name of the chart.
*/}}
{{- define "config-center.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "config-center.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "config-center.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "config-center.labels" -}}
helm.sh/chart: {{ include "config-center.chart" . }}
{{ include "config-center.selectorLabels" . }}
app.frontegg.io/version: {{ .Chart.Version | quote }}
app.frontegg.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "config-center.selectorLabels" -}}
app.frontegg.com/name: {{ include "config-center.name" . }}
app.frontegg.com/instance: {{ .Release.Name }}
{{- end -}}

{{- define "add-headers-yaml" -}}
{{- $input := . -}}
add:
  headers:
    - "x-frontegg-api-key: {{ $input }}"
{{- end }}

{{- $top := . }}
{{- $values := .Values }}
vendorService:
  url: {{ $values.frontegg.services.vendorsServiceUrl }}.frontegg.svc.cluster.local
identityService:
  url: {{ $values.frontegg.services.identityServiceUrl }}.frontegg.svc.cluster.local
redis:
  dbIndex: 0
kafka:
  usageReportingTopic: {{ $values.frontegg.applications.tenants.tenantsUsageReportingTopicName | quote }}
multiHost:
  enableMultiHost: {{ $values.frontegg.applications.apiGateway.enableMultiHosts }}
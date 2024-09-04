{{/* Just the name */}}
{{- define "name" -}}
{{- required "I cant live without a name: .Values.name must be set" .Values.name }}{{ include "suffix" . }}
{{- end -}}

{{/* calculate the suffix */}}
{{- define "suffix" -}}
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
- name: secret-volume
  mountPath: {{ .Values.externalSecret.mountPath }}
  subPath: {{ .Values.externalSecret.subPath }} 
{{- end -}}

{{/* general labels for resources not related to web/hp/worker */}}
{{- define "labels" -}}
helm.sh/chart: {{ include "unified.chart" . }}
app.frontegg.io/version: {{ .Chart.Version | quote }}
app.frontegg.io/managed-by: {{ .Release.Service }}
app.frontegg.com/team: {{ required "Every service needs to have responsible parents. .Values.team is required." .Values.team }}
app.frontegg.com/appVersion: {{ include "appVersion" . | quote }}
{{- end -}}

{{- define "web.labels" -}}
app.frontegg.com/team: {{ required ".Values.team is required" .Values.team }}
app.frontegg.com/appVersion: {{ include "appVersion" . | quote }}
{{- with .Values.web.labels }}
{{ toYaml . }}
{{- end }}
{{ include "web.selector.labels" . }}
{{- end -}}

{{/* Selector labels */}}
{{- define "web.selector.labels" -}}
app.frontegg.com/name: {{ include "name" . }}-web
{{- end -}}

{{- define "job.labels" -}}
app.frontegg.com/name: {{ include "name" . }}-job
app.frontegg.com/instance: {{ .Release.Name }}
{{- end -}}

{{- define "cronjob.labels" -}}
app.frontegg.com/name: {{ include "name" . }}-cronjob
app.frontegg.com/instance: {{ .Release.Name }}
{{- end -}}

{{- define "worker.labels" -}}
app.frontegg.com/team: {{ required ".Values.team is required" .Values.team }}
app.frontegg.com/appVersion: {{ include "appVersion" . | quote }}
{{- with .Values.worker.labels }}
{{ toYaml . }}
{{- end }}
{{ include "worker.selector.labels" . }}
{{- end -}}

{{- define "worker.selector.labels" -}}
app.frontegg.com/name: {{ include "name" . }}-worker
{{- end -}}

{{- define "appVersion" -}}
{{ required "NEED APPVERSION: .Values.appVersion is required cant run without it" .Values.appVersion }}
{{- end -}}

{{- define "secret.name" -}}
{{ include "name" . }}-{{ include "appVersion" . }}
{{- end -}}

{{/*
Common labels includes HP selector.labels
*/}}
{{- define "hp.labels" -}}
app.frontegg.com/team: {{ .Values.team }}
helm.sh/chart: {{ include "unified.chart" . }}
app.frontegg.io/version: {{ .Chart.Version | quote }}
app.frontegg.io/managed-by: {{ .Release.Service }}
app.frontegg.com/appVersion: {{ include "appVersion" . | quote }}
{{ include "hp.selector.labels" . }}
{{- end -}}

{{/*
Selector labels for high priority pods
*/}}
{{- define "hp.selector.labels" -}}
app.frontegg.com/name: {{ include "name" . }}-hp
{{- end -}}

{{- define "keda.annotations" -}}
{{- .Values.keda.annotations | toYaml }}
{{- end -}}

{{/* what is linkerd? */}}
{{- define "linkerd.annotations" -}}
{{ .Values.linkerd.annotations }}
{{- end -}}

{{- define "calculate.pod.annotations" -}}
{{- if .linkerd.enabled }}
{{- mergeOverwrite .podAnnotations .linkerd.annotations | toYaml }}
{{- else }}
{{- if .podAnnotations }}
{{- $result := .podAnnotations }}
{{- range $k := keys .linkerd.annotations -}}
{{- $_ := unset $result $k }}
{{- end -}}
{{- toYaml $result }}
{{- end }}
{{- end }}
{{- end -}}

{{/* service account name from values or generate it */}}
{{- define "service.account.name" -}}
{{ .Values.serviceAccount.nameOverride | default (include "name" . )}}
{{- end -}}

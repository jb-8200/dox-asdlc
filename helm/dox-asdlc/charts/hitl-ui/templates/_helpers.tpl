{{/*
Expand the name of the chart.
*/}}
{{- define "hitl-ui.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "hitl-ui.fullname" -}}
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

{{/*
Get parent release name for referencing parent secrets.
*/}}
{{- define "hitl-ui.parentFullname" -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "hitl-ui.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "hitl-ui.labels" -}}
helm.sh/chart: {{ include "hitl-ui.chart" . }}
{{ include "hitl-ui.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: hitl-ui
app.kubernetes.io/part-of: dox-asdlc
{{- end }}

{{/*
Selector labels
*/}}
{{- define "hitl-ui.selectorLabels" -}}
app.kubernetes.io/name: {{ include "hitl-ui.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

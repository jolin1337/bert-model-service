{{/*
Expand the name of the chart.
*/}}
{{- define "blv-app-template.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "blv-app-template.fullname" -}}
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
Create chart name and version as used by the chart label.
*/}}
{{- define "blv-app-template.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "blv-app-template.labels" -}}
helm.sh/chart: {{ include "blv-app-template.chart" . }}
{{ include "blv-app-template.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}

{{- end }}

{{/*
Selector labels
*/}}
{{- define "blv-app-template.selectorLabels" -}}
app.kubernetes.io/name: {{ include "blv-app-template.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Application metadata
*/}}
{{- define "blv-app-template.applicationMetadata" -}}
{{- $errorMessage := "The mandatory #VALUE# is missing!" -}}
app.bolagsverket.se/description: {{ required (print ($errorMessage | replace "#VALUE#" ".Values.app.description")) .Values.app.description }}
app.bolagsverket.se/owner: {{ required (print ($errorMessage | replace "#VALUE#" ".Values.app.owner" )) .Values.app.owner }}
app.bolagsverket.se/documentation: {{ required (print ($errorMessage | replace "#VALUE#" ".Values.app.documentation" )) .Values.app.documentation }}
app.bolagsverket.se/repository: {{ required (print ($errorMessage | replace "#VALUE#" ".Values.app.repository" )) .Values.app.repository }}
app.bolagsverket.se/runbook: {{ required (print ($errorMessage | replace "#VALUE#" ".Values.app.runbook" )) .Values.app.runbook }}

{{- if .Values.app.chat }}
app.bolagsverket.se/chat: {{ .Values.app.chat }}
{{- end }}
{{- if .Values.app.incidents }}
app.bolagsverket.se/incidents: {{ .Values.app.incidents }}
{{- end }}
{{- if .Values.app.uptime }}
app.bolagsverket.se/uptime: {{ .Values.app.uptime }}
{{- end }}
{{- if .Values.app.performance }}
app.bolagsverket.se/performance: {{ .Values.app.performance }}
{{- end }}
{{- if .Values.app.dependencies }}
app.bolagsverket.se/dependencies: {{ .Values.app.dependencies }}
{{- end }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "blv-app-template.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "blv-app-template.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Get blvEnvModeNr
*/}}
{{- define "blv-app-template.blvEnvModeNr" -}}
{{- required "A valid .Values.blvEnvModeNr entry required!" .Values.blvEnvModeNr }}
{{- end }}

{{/*
Get blvEnvMode
*/}}
{{- define "blv-app-template.blvEnvMode" -}}
{{- required "A valid .Values.blvEnvMode entry required!" .Values.blvEnvMode }}
{{- end }}

{{/*
DNS internal domain suffix
*/}}
{{- define "blv-app-template.fqdnSuffixInternal" -}}
{{- $blvEnvModeNr := (include "blv-app-template.blvEnvModeNr" .) -}}
{{- if eq $blvEnvModeNr "prod" }}
{{- .Values.fqdnSuffixInternal | default ".prod.bolagsverket.se" }}
{{- else }}
{{- .Values.fqdnSuffixInternal | default (printf "-%s.%s.bolagsverket.se" $blvEnvModeNr $blvEnvModeNr) }}
{{- end }}
{{- end }}

{{/*
DNS external domain suffix
*/}}
{{- define "blv-app-template.fqdnSuffixExternal" -}}
{{- $blvEnvModeNr := (include "blv-app-template.blvEnvModeNr" .) -}}
{{- if eq $blvEnvModeNr "prod" }}
{{- .Values.fqdnSuffixExternal | default ".bolagsverket.se" }}
{{- else }}
{{- .Values.fqdnSuffixExternal | default (printf "-%s.bolagsverket.se" $blvEnvModeNr) }}
{{- end }}
{{- end }}

{{- define "blv-app-template._ingressHostSuffix" -}}
{{- if .Values.ingressHostSuffixExternal  }}
{{- include "blv-app-template.fqdnSuffixExternal" . }}
{{- else }}
{{- include "blv-app-template.fqdnSuffixInternal" . }}
{{- end }}
{{- end }}

{{- define "blv-app-template.ingressHostSuffix" -}}
{{- .Values.ingressHostSuffix | default (include "blv-app-template._ingressHostSuffix" .)  }}
{{- end }}

{{/*
BLV Environment variables
*/}}
{{- define "blv-app-template.blvEnvs" -}}
- name: BLV_ENV_MODE
  value: {{ include "blv-app-template.blvEnvMode" . }}
- name: BLV_ENV_MODE_NR
  value: {{ include "blv-app-template.blvEnvModeNr" . }}
- name: BLV_FQDN_SUFFIX_INTERNAL
  value: {{ include "blv-app-template.fqdnSuffixInternal" . }}
- name: BLV_FQDN_SUFFIX_EXTERNAL
  value: {{ include "blv-app-template.fqdnSuffixExternal" . }}
{{- end }}

{{/*
IBM MQ Environment variables
*/}}
{{- define "blv-app-template.mqEnvs" -}}
- name: BLV_MQ_CONNECTNAMES
{{- if eq .Values.blvEnvMode "accept" "prod" }}
  value: {{ .Values.ibm.mq.connectnames | default "bv-mq-01(1414),bv-mq-02(1414)" }}
{{- else if eq .Values.blvEnvMode "utv" }}
  {{- if eq .Values.blvEnvModeNr "utv01" "utv" }}
  value: {{ .Values.ibm.mq.connectnames | default "bv-mq-01(1414)" }}
  {{- else if eq .Values.blvEnvModeNr "utv02" }}
  value: {{ .Values.ibm.mq.connectnames | default "bv-mq-01(1415)" }}
  {{- else if eq .Values.blvEnvModeNr "utv03" }}
  value: {{ .Values.ibm.mq.connectnames | default "bv-mq-01(1416)" }}
  {{- else if eq .Values.blvEnvModeNr "utv04" }}
  value: {{ .Values.ibm.mq.connectnames | default "bv-mq-01(1417)" }}
  {{- end}}
{{- else }}
  value: {{ .Values.ibm.mq.connectnames | default "bv-mq-01(1414)" }}
{{- end }}
- name: BLV_MQ_QUEUEMANAGER
{{- if eq .Values.blvEnvMode "utv" }}
  {{- if eq .Values.blvEnvModeNr "utv01" "utv" }}
  value: {{ .Values.ibm.mq.queuemanager | default "UTV01" }}
  {{- else if eq .Values.blvEnvModeNr "utv02" }}
  value: {{ .Values.ibm.mq.queuemanager | default "UTV02" }}
  {{- else if eq .Values.blvEnvModeNr "utv03" }}
  value: {{ .Values.ibm.mq.queuemanager | default "UTV03" }}
  {{- else if eq .Values.blvEnvModeNr "utv04" }}
  value: {{ .Values.ibm.mq.queuemanager | default "UTV04" }}
  {{- end}}
{{- else }}
  value: {{ .Values.ibm.mq.queuemanager | default (print "QMGR" (include "blv-app-template.blvEnvModeNr" . )) | upper }}
{{- end }}
- name: BLV_MQ_CHANNEL
  value: {{ required "A valid .Values.ibm.mq.channel entry required!" .Values.ibm.mq.channel }}
{{- if .Values.ibm.mq.user }}
- name:  BLV_MQ_USERNAME
  value: {{ .Values.ibm.mq.user }}
{{- end }}
{{- if .Values.ibm.mq.password }}
- name:  BLV_MQ_PASSWORD
  value: {{ .Values.ibm.mq.password | quote }}
{{- end }}
{{- end }}

{{/*
Oracle TNS_ADMIN environment variable
*/}}
{{- define "blv-app-template.oracleTnsAdminEnv" -}}
- name: TNS_ADMIN
  value: {{ .Values.oracle.tnsnames.mountPath }}
{{- end }}

{{/*
Kafka Environment variables
*/}}
{{- define "blv-app-template.kafkaEnvs" -}}
- name: BLV_KAFKA_CONNECTNAMES
{{- if eq .Values.blvEnvMode "accept" "prod" }}
  value: {{ .Values.kafka.connectnames | default "bv-kafka-01:9092,bv-kafka-02:9092,bv-kafka-03:9092" }}
{{- else }}
  value: {{ .Values.kafka.connectnames | default "bv-kafka-01:9092" }}
{{- end }}
{{- end }}

{{/*
ZooKeeper Environment variables.
*/}}
{{- define "blv-app-template.zookeeperEnvs" -}}
- name: BLV_ZOOKEEPER_CONNECTNAMES
  value: {{ .Values.zookeeper.connectnames | default "bv-zookeeper-01:2281,bv-zookeeper-02:2281,bv-zookeeper-03:2281" }}
{{- end }}

{{- define "pcfb.labels" -}}
app: pcfb
env: {{ required "env is required" .Values.env }}
{{- end }}

{{- define "pcfb.image" -}}
{{ .root.Values.image.registry }}/{{ .name }}:{{ required "image.tag is required" .root.Values.image.tag }}
{{- end }}

{{- define "pcfb.backendEnv" -}}
- name: AUTO_BOOTSTRAP
  value: "false"
- name: REFRESH_INTERVAL_HOURS
  value: "0"
- name: HISTORY_SEASONS
  value: {{ .Values.historySeasons | quote }}
{{- end }}

{{- define "pcfb.backendSecurity" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
runAsNonRoot: true
runAsUser: 10001
capabilities: {drop: [ALL]}
seccompProfile: {type: RuntimeDefault}
{{- end }}

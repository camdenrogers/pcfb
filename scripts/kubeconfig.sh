#!/bin/bash
# Writes ~/.kube/pcfb.yaml from the server. Use it with: export KUBECONFIG=~/.kube/pcfb.yaml
set -euo pipefail
PROJECT=pcfb-platform ZONE=us-central1-a
VM=$(gcloud compute instance-groups managed list-instances pcfb-server \
  --project "$PROJECT" --zone "$ZONE" --format='value(instance.basename())' | head -1)
[ -n "$VM" ] || { echo "no server instance found" >&2; exit 1; }
mkdir -p ~/.kube
umask 077
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT
gcloud compute ssh "$VM" --tunnel-through-iap --project "$PROJECT" --zone "$ZONE" --quiet \
  --ssh-key-expire-after=15m \
  --command 'sudo cat /etc/rancher/k3s/k3s.yaml' |
  sed -n '/^apiVersion: v1$/,$p' | sed 's/: default$/: pcfb/' >"$TMP"
grep -q 'server: https://127.0.0.1:6443' "$TMP"
mv "$TMP" ~/.kube/pcfb.yaml
echo "wrote ~/.kube/pcfb.yaml"

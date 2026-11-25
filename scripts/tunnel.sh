#!/bin/bash
# Forwards localhost:6443 to the k3s API server through IAP. Leave it running while using kubectl.
set -euo pipefail
PROJECT=pcfb-platform ZONE=us-central1-a
VM=$(gcloud compute instance-groups managed list-instances pcfb-server \
  --project "$PROJECT" --zone "$ZONE" --format='value(instance.basename())' | head -1)
[ -n "$VM" ] || { echo "no server instance found" >&2; exit 1; }
exec gcloud compute start-iap-tunnel "$VM" 6443 --local-host-port=localhost:6443 --project "$PROJECT" --zone "$ZONE"

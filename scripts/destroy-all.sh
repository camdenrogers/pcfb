#!/bin/bash
# Deletes the whole platform, including both databases and the k3s state disk. This can't be undone.
#   scripts/destroy-all.sh --dry-run   show what would be destroyed
#   scripts/destroy-all.sh             destroy it, after typed confirmation
# Bootstrap (state bucket, CI identities, budget) stays. docs/platform.md covers removing it.
set -euo pipefail
PROJECT=pcfb-platform
ROOT=$(cd "$(dirname "$0")/.." && pwd)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

NEON_API_KEY=$(gcloud secrets versions access latest --secret=ci-neon-api-key --project "$PROJECT")
CLOUDFLARE_API_TOKEN=$(gcloud secrets versions access latest --secret=ci-cloudflare-api-token --project "$PROJECT")
export NEON_API_KEY CLOUDFLARE_API_TOKEN

# prevent_destroy can't be overridden from the command line, so work on a copy without it.
cp -R "$ROOT/infra/platform" "$WORK/platform"
rm -rf "$WORK/platform/.terraform"
for f in "$WORK"/platform/*.tf; do
  sed 's/prevent_destroy = true/prevent_destroy = false/' "$f" >"$f.new"
  mv "$f.new" "$f"
done
tf() { terraform -chdir="$WORK/platform" "$@"; }
tf init -input=false >/dev/null

if [ "${1:-}" = --dry-run ]; then
  tf plan -destroy -input=false -lock=false
  exit
fi

read -r -p "This deletes the cluster and BOTH databases. Type 'destroy $PROJECT' to continue: " answer
[ "$answer" = "destroy $PROJECT" ] || { echo "cancelled"; exit 1; }

# The VMs go first: Cloudflare won't delete a tunnel that still has live connections.
tf destroy -input=false -auto-approve \
  -target=google_compute_instance_group_manager.agent \
  -target=google_compute_instance_group_manager.server
tf destroy -input=false -auto-approve
gcloud storage rm "gs://$PROJECT-tfstate/cluster/default.tfstate"
echo "Done. Only the bootstrap resources remain."

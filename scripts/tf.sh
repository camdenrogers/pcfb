#!/bin/bash
# Runs terraform in infra/platform with provider tokens from Secret Manager, e.g. scripts/tf.sh plan
set -euo pipefail
PROJECT=pcfb-platform
NEON_API_KEY=$(gcloud secrets versions access latest --secret=ci-neon-api-key --project "$PROJECT")
CLOUDFLARE_API_TOKEN=$(gcloud secrets versions access latest --secret=ci-cloudflare-api-token --project "$PROJECT")
export NEON_API_KEY CLOUDFLARE_API_TOKEN
exec terraform -chdir="$(dirname "$0")/../infra/platform" "$@"

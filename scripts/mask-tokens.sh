#!/bin/bash
# Registers the provider tokens as masked in GitHub Actions. Its output must never be redirected to a file.
# With --check FILE, fails instead if FILE contains either token.
set -euo pipefail
for secret in ci-neon-api-key ci-cloudflare-api-token; do
  value=$(gcloud secrets versions access latest --secret="$secret" --project pcfb-platform)
  [ -n "$value" ] || { echo "$secret is empty" >&2; exit 1; }
  if [ "${1:-}" = --check ]; then
    if grep -qF -- "$value" "$2"; then
      echo "refusing: $2 contains $secret" >&2
      exit 1
    fi
  elif [ "${GITHUB_ACTIONS:-}" = true ]; then
    echo "::add-mask::$value"
  fi
done

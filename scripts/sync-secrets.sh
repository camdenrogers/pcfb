#!/bin/bash
# Copies generated credentials into Secret Manager without printing them or storing them in Terraform.
#   scripts/sync-secrets.sh neon test|prod
#   scripts/sync-secrets.sh tunnel
set -euo pipefail
PROJECT=pcfb-platform
ROOT=$(cd "$(dirname "$0")/.." && pwd)

read_secret() { gcloud secrets versions access latest --secret="$1" --project "$PROJECT" 2>/dev/null; }
output() { terraform -chdir="$ROOT/infra/platform" output -json "$1"; }
field() { python3 -c 'import json,sys
v = json.load(sys.stdin)
for k in sys.argv[1:]: v = v[k]
print(v)' "$@"; }
# The header goes through a file descriptor so the token never shows up in `ps`.
api() { curl -sf --config <(printf 'header = "Authorization: Bearer %s"\n' "$1") "$2"; }

store() {
  if [ "$(read_secret "$1" || true)" = "$2" ]; then
    echo "$1 is already current"
    return
  fi
  printf %s "$2" | gcloud secrets versions add "$1" --data-file=- --project "$PROJECT" >/dev/null
  echo "$1 updated"
}

case "${1:-}" in
  neon)
    ENV=${2:?test or prod}
    INFO=$(output neon)
    PID=$(field "$ENV" project_id <<<"$INFO")
    BRANCH=$(field "$ENV" branch_id <<<"$INFO")
    HOST=$(field "$ENV" host <<<"$INFO")
    ROLE=$(field "$ENV" role <<<"$INFO")
    DB=$(field "$ENV" database <<<"$INFO")
    PASSWORD=$(api "$(read_secret ci-neon-api-key)" \
      "https://console.neon.tech/api/v2/projects/$PID/branches/$BRANCH/roles/$ROLE/reveal_password" | field password)
    ENCODED=$(printf %s "$PASSWORD" | python3 -c 'import sys,urllib.parse; print(urllib.parse.quote(sys.stdin.read(), safe=""))')
    store "database-url-$ENV" "postgresql+psycopg://$ROLE:$ENCODED@$HOST/$DB?sslmode=require"
    ;;
  tunnel)
    INFO=$(output tunnel)
    TOKEN=$(api "$(read_secret ci-cloudflare-api-token)" \
      "https://api.cloudflare.com/client/v4/accounts/$(field account_id <<<"$INFO")/cfd_tunnel/$(field tunnel_id <<<"$INFO")/token" | field result)
    store cloudflare-tunnel-token "$TOKEN"
    ;;
  *)
    sed -n '3,4p' "$0"
    exit 1
    ;;
esac

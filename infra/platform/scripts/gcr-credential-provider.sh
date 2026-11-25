#!/bin/bash
# Kubelet credential provider: trades the node's metadata token for Artifact Registry credentials.
set -euo pipefail
cat >/dev/null
TOKEN=$(curl -sf -H 'Metadata-Flavor: Google' \
  http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token |
  python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
cat <<JSON
{"apiVersion":"credentialprovider.kubelet.k8s.io/v1","kind":"CredentialProviderResponse","cacheKeyType":"Registry","cacheDuration":"4m0s","auth":{"REGISTRY_HOST":{"username":"oauth2accesstoken","password":"$TOKEN"}}}
JSON

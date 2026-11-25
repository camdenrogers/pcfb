#!/bin/bash
# Publishes the chart as of a commit, with its image tag, to the env/<env> branch that ArgoCD tracks.
#   scripts/publish-env.sh test|prod <full commit SHA>
set -euo pipefail
ENV=${1:?environment} SHA=${2:?commit SHA}
[[ "$ENV" =~ ^(test|prod)$ ]] || { echo "unknown environment: $ENV" >&2; exit 1; }
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || { echo "not a full SHA: $SHA" >&2; exit 1; }
BRANCH=env/$ENV
WORK=$(mktemp -d)
trap 'git worktree remove --force "$WORK/tree" 2>/dev/null || true; rm -rf "$WORK"' EXIT

if git fetch -q origin "$BRANCH" 2>/dev/null; then
  git worktree add -q --detach "$WORK/tree" FETCH_HEAD
else
  git worktree add -q --detach "$WORK/tree" "$SHA"
  git -C "$WORK/tree" checkout -q --orphan "publish-$ENV"
fi
git -C "$WORK/tree" rm -rqf --ignore-unmatch .
mkdir -p "$WORK/tree/chart"
git archive "$SHA:deploy/charts/pcfb" | tar -x -C "$WORK/tree/chart"
printf 'image:\n  tag: "%s"\n' "$SHA" >"$WORK/tree/chart/image-tag.yaml"
echo "$SHA" >"$WORK/tree/DEPLOYED_SHA"

git -C "$WORK/tree" add -A
if git -C "$WORK/tree" diff --cached --quiet; then
  echo "$BRANCH already at $SHA"
  exit 0
fi
git -C "$WORK/tree" -c user.name='github-actions[bot]' \
  -c user.email='41898282+github-actions[bot]@users.noreply.github.com' \
  commit -q -m "Deploy ${SHA:0:7} to $ENV"
git -C "$WORK/tree" push -q origin "HEAD:refs/heads/$BRANCH"
echo "$BRANCH now at $SHA"

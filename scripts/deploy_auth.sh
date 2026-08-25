#!/usr/bin/env bash
# Deploy step auth: DEPLOY_TOKEN is the private half of a deploy key registered
# on the deploy target repo. Fails the job if the target rejects it.
set -euo pipefail
: "${DEPLOY_TOKEN:?DEPLOY_TOKEN is not set}"
: "${DEPLOY_TARGET:?DEPLOY_TARGET is not set}"
keyfile="$(mktemp)"
trap 'rm -f "$keyfile"' EXIT
chmod 600 "$keyfile"
printf '%s\n' "$DEPLOY_TOKEN" > "$keyfile"
GIT_SSH_COMMAND="ssh -i $keyfile -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" \
  git ls-remote "git@github.com:${DEPLOY_TARGET}.git" HEAD > /dev/null
echo "deploy target ${DEPLOY_TARGET}: authenticated"

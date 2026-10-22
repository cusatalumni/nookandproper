#!/usr/bin/env bash
# Build and push the site to GitHub, tolerating concurrent commits made on github.com.
set -e
cd "$(dirname "$0")"
export GIT_SSH_COMMAND="ssh -i $HOME/agent-state/.deploy/nook_ed25519 -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
MSG="${1:-daily pins $(date -u +%Y-%m-%d)}"

python3 build.py
git add -A
git -c user.email=deploy@nookandproper -c user.name="Nook and Proper" commit -m "$MSG" >/dev/null 2>&1 || true

git fetch -q origin main
if ! git merge-base --is-ancestor origin/main HEAD 2>/dev/null; then
  echo "remote moved — rebuilding on top of origin/main"
  git reset --mixed -q origin/main
  git add -A
  git -c user.email=deploy@nookandproper -c user.name="Nook and Proper" commit -m "$MSG" >/dev/null 2>&1 || true
fi
git push -q origin HEAD:main
echo "pushed $(git rev-parse --short HEAD) to main"

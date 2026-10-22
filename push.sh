#!/usr/bin/env bash
# Push the built site to GitHub. Repo URL comes from .git/config (origin).
set -e
cd "$(dirname "$0")"
export GIT_SSH_COMMAND="ssh -i $HOME/agent-state/.deploy/nook_ed25519 -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
python3 build.py
git add -A
git -c user.email=deploy@nookandproper -c user.name="Nook and Proper" commit -m "${1:-daily pins $(date -u +%Y-%m-%d)}" || echo "nothing to commit"
git push origin HEAD:main

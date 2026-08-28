#!/usr/bin/env bash
set -euo pipefail

readonly ALLOWED='https://github.com/Olivermugambi/ameru-cultural-library-backend.git'
readonly SSH_ALLOWED='git@github.com:Olivermugambi/ameru-cultural-library-backend.git'

current="$(git remote get-url origin)"
push="$(git remote get-url --push origin)"
case "$current" in "$ALLOWED"|"$SSH_ALLOWED") ;; *) exit 77 ;; esac
case "$push" in "$ALLOWED"|"$SSH_ALLOWED") ;; *) exit 77 ;; esac

if [[ "$(git remote | wc -l | tr -d ' ')" != 1 ]]; then
  printf 'PROJECT POLICY: only the canonical origin remote is permitted.\n' >&2
  exit 77
fi

chmod +x .project-policy/git-guard .githooks/pre-push
git config --local core.hooksPath .githooks
printf 'Repository boundary active: Olivermugambi/ameru-cultural-library-backend\n'

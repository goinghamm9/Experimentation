#!/usr/bin/env bash
# SessionStart hook: make the Codex plugin usable in Claude Code cloud sessions.
#
# Cloud VMs start from a fresh clone, so Codex is not installed and not logged
# in. This installs it if missing and logs in with OPENAI_API_KEY. It is a
# no-op on a local machine (CLAUDE_CODE_REMOTE unset), when the key is absent,
# or when Codex is already logged in. It never fails the session.
set -u

[ -n "${CLAUDE_CODE_REMOTE:-}" ] || exit 0
[ -n "${OPENAI_API_KEY:-}" ] || exit 0

if ! command -v codex >/dev/null 2>&1; then
  npm install -g @openai/codex >/dev/null 2>&1 || exit 0
fi

if codex login status >/dev/null 2>&1; then
  exit 0
fi

printenv OPENAI_API_KEY | codex login --with-api-key >/dev/null 2>&1 || true
exit 0

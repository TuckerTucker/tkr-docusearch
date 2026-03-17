#!/usr/bin/env bash
set -euo pipefail

HOOK_NAME="${1:-}"
if [[ -z "$HOOK_NAME" ]]; then
  exit 1
fi

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
HOOK_PATH="$PROJECT_ROOT/tkr-kit/core/hooks/${HOOK_NAME}.ts"
BUN_PATH="$(command -v bun)" || exit 1

[[ -f "$HOOK_PATH" ]] || exit 1

exec "$BUN_PATH" "$HOOK_PATH"

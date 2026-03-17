#!/usr/bin/env bash
# MCP stale-code detector
# Checks if MCP tool source files have been modified since the MCP server started.
# Used as a PreToolUse hook on mcp__product-surface__* tool calls.
#
# Exit 0 = no issue (hook passes)
# Outputs warning to stdout if stale files detected (shown to user inline)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MARKER="$SCRIPT_DIR/.tkr-kit/mcp-started-at"

# No marker = server hasn't written one yet (first run or old version)
if [ ! -f "$MARKER" ]; then
  exit 0
fi

# Find .ts files in mcp/ modified after the marker file
STALE=$(find "$SCRIPT_DIR/mcp" -name "*.ts" -newer "$MARKER" -not -path "*/__tests__/*" -not -path "*/node_modules/*" 2>/dev/null | head -5)

if [ -n "$STALE" ]; then
  COUNT=$(echo "$STALE" | wc -l | tr -d ' ')
  FILES=$(echo "$STALE" | sed "s|$SCRIPT_DIR/||g" | tr '\n' ', ' | sed 's/,$//')
  echo "WARNING: MCP server is running stale code. $COUNT file(s) modified since server started: $FILES. Run /mcp to reconnect."
fi

exit 0

#!/usr/bin/env bash
# MCP runner for product-surface server
# Resolves to project root and launches the stdio MCP server via Bun.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec bun run "$PROJECT_ROOT/tkr-kit/mcp/server.ts"

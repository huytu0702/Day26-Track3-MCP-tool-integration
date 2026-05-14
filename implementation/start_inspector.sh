#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$ROOT/.venv/Scripts/python.exe"

NPM_CONFIG_CACHE="$ROOT/.npm-cache" \
npx -y @modelcontextprotocol/inspector \
  "$PYTHON" \
  -m \
  implementation.mcp_server

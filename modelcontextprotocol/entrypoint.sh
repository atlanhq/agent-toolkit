#!/usr/bin/env bash
# entrypoint.sh - Entrypoint for the Atlan MCP server container

set -euo pipefail

# Default values are provided for ease of local testing.
: "${MCP_TRANSPORT:=stdio}"
: "${MCP_HOST:=0.0.0.0}"
: "${MCP_PORT:=8000}"
: "${MCP_PATH:=/}"

exec python server.py --transport "${MCP_TRANSPORT}" \
                      --host "${MCP_HOST}" \
                      --port "${MCP_PORT}" \
                      --path "${MCP_PATH}"

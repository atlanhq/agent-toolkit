# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Atlan Agent Toolkit — a monorepo containing tools and protocols for AI agents to interact with Atlan services. Two main components:

1. **MCP Server** (`modelcontextprotocol/`) — Python FastMCP server exposing 15+ tools for Atlan asset search, lineage, governance, glossary, data mesh, and data quality via pyatlan SDK
2. **Claude Plugin** (`claude-plugin/`) — Claude Code plugin providing OAuth 2.1 access to Atlan's data catalog through MCP

## Build and Development Commands

### MCP Server (`modelcontextprotocol/`)
```bash
# Install dependencies
cd modelcontextprotocol && uv sync

# Run MCP server (stdio mode)
uv run python server.py

# Run with Docker
docker build -t atlan-mcp-server modelcontextprotocol/
docker run --env-file modelcontextprotocol/.env atlan-mcp-server

# Run client test
uv run python client.py
```

### Claude Plugin (`claude-plugin/`)
```bash
# Plugin is declarative — no build step
# Install in Claude Code via /mcp command
```

### Pre-commit
```bash
pre-commit install
pre-commit run --all-files
```

## Architecture

```
agent-toolkit/
├── modelcontextprotocol/       # Python MCP server
│   ├── server.py               # Main FastMCP server — tool registration & handlers
│   ├── middleware.py            # Auth middleware (OAuth 2.1)
│   ├── settings.py             # Configuration from env vars
│   ├── tools/                  # Tool implementations (one file per domain)
│   ├── utils/                  # Shared utilities
│   ├── client.py               # Test client
│   ├── Dockerfile              # Production container
│   ├── .env.template           # Environment variable template
│   └── pyproject.toml          # Python dependencies (uv)
├── claude-plugin/              # Claude Code plugin
│   ├── .claude-plugin/         # Plugin manifest
│   │   └── plugin.json         # Plugin definition
│   ├── .mcp.json               # MCP server connection config
│   ├── CLAUDE.md               # Plugin-specific Claude guidance
│   └── README.md               # Plugin documentation
├── .github/                    # CI/CD workflows
├── CONTRIBUTING.md             # Contribution guidelines
└── commitlint.config.js        # Commit message linting
```

## Environment Variables

Required (MCP Server):
- `ATLAN_API_KEY` — Atlan API key for pyatlan SDK authentication
- `ATLAN_BASE_URL` — Atlan instance URL

See `modelcontextprotocol/.env.template` for full list.

## Code Conventions

- Python code uses `uv` for dependency management
- MCP tools follow FastMCP patterns with typed parameters
- Tool names use `snake_case` (e.g., `semantic_search_tool`)
- Commit messages follow conventional commits (enforced by commitlint)
- Pre-commit hooks for code quality

---

## Security

### Security Rules
1. **No hardcoded secrets** — `ATLAN_API_KEY`, OAuth secrets, and all credentials must come from environment variables or OAuth flows; never in source code, configs, or tool responses
2. **OAuth tokens are ephemeral** — OAuth 2.1 tokens from the Claude Plugin flow must not be stored in files, logs, or committed; the authentication middleware handles token lifecycle
3. **No secrets in tool responses** — MCP tool output must never include API keys, OAuth tokens, connection strings, or internal service URLs with embedded credentials
4. **Sanitize all tool inputs** — validate and sanitize all parameters passed to pyatlan SDK calls; never pass unsanitized user input to asset queries or DSL
5. **No secrets in Docker layers** — multi-stage builds; credentials via env vars or mounted secrets only
6. **No secrets in logs** — never log auth tokens, API keys, or full request/response bodies containing auth headers
7. **Plugin manifests are credential-free** — `plugin.json`, `.mcp.json` must never contain secrets or real API endpoints with auth tokens
8. **Dependency pinning** — `uv.lock` must be committed; review dependency updates for supply chain risks

### Secret Discovery Protocol
Before writing any code, check for secrets/credentials:
1. `.env` / `.env.template` — never commit `.env`; template must use placeholder values only
2. `modelcontextprotocol/server.py` — scan for hardcoded API keys, Atlan tokens, or connection strings
3. `modelcontextprotocol/settings.py` — verify all config comes from env vars
4. `modelcontextprotocol/middleware.py` — check auth middleware for token leakage
5. `modelcontextprotocol/tools/` — check tool implementations for embedded credentials
6. `claude-plugin/.mcp.json` — verify no secrets in MCP connection config
7. `claude-plugin/.claude-plugin/plugin.json` — verify no credentials in plugin manifest
8. Docker/CI configs — verify no secrets in build args, workflow files, or image layers

**If you find a secret:** STOP. Do not commit it, do not include it in any output.

### Severity Classification
- **CRITICAL**: OAuth tokens in code/logs, API keys in source, secrets in tool responses, credentials in plugin manifests
- **HIGH**: Missing input validation on MCP tool parameters, secrets in Docker layers, unsanitized DSL queries
- **MEDIUM**: Verbose error messages exposing internal infrastructure, missing rate limiting, overly permissive CORS
- **LOW**: Missing request logging, inconsistent error response formats, missing security headers
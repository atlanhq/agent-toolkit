# AGENTS.md

## Project Overview

Atlan Agent Toolkit — a collection of tools and protocols for AI agents to interact with Atlan services. Contains two main components:

1. **MCP Server** (`modelcontextprotocol/`) — Python-based Model Context Protocol server providing tools for asset search, discovery, lineage, governance, and data quality management via [pyatlan](https://developer.atlan.com/sdks/python/)
2. **Claude Plugin** (`claude-plugin/`) — Claude Code plugin enabling OAuth-based access to Atlan's data catalog through MCP tools

## Security

### Security Invariants
1. **No hardcoded secrets** — API keys, OAuth secrets, Atlan tokens, and all credentials must come from environment variables or OAuth flows; never in source code, configs, or tool responses
2. **OAuth tokens are ephemeral** — OAuth 2.1 tokens must not be stored in files, logs, or committed to the repository; the authentication flow handles token lifecycle
3. **No secrets in tool responses** — MCP tool output must never include API keys, OAuth tokens, connection strings, or internal service URLs with embedded credentials
4. **No secrets in Docker layers** — use multi-stage builds; credentials via env vars or mounted secrets only; never bake into images
5. **No secrets in logs** — structured logging only; never log auth tokens, API keys, user credentials, or full request/response bodies containing auth headers
6. **Sanitize all tool inputs** — validate and sanitize all parameters passed to pyatlan SDK calls and MCP tools; never pass unsanitized user input to asset queries or DSL
7. **Plugin manifests are credential-free** — `plugin.json`, `.mcp.json`, and all manifest files must never contain secrets or real API endpoints with auth tokens
8. **Dependency pinning** — lock files must be committed; review all dependency updates for supply chain risks before merging

### Security Review Checklist
- [ ] No API keys, tokens, or credentials in source code
- [ ] `.env.template` uses placeholder values only; `.env` is gitignored
- [ ] OAuth flow does not leak tokens in logs, URLs, or error messages
- [ ] MCP tool responses sanitized — no credentials in output
- [ ] Docker builds use multi-stage; no secrets baked in
- [ ] All tool input parameters validated before SDK calls
- [ ] Plugin manifests contain no embedded credentials
- [ ] Dependencies reviewed for known vulnerabilities
- [ ] CI/CD workflows do not echo secrets

### Secret Discovery Protocol
Before writing any code, check for secrets/credentials:
1. `.env` / `.env.template` — never commit `.env`; template must use placeholder values only
2. `modelcontextprotocol/server.py` — scan for hardcoded API keys, Atlan tokens, or connection strings
3. `modelcontextprotocol/settings.py` — verify all config comes from env vars
4. `modelcontextprotocol/tools/` — check tool implementations for embedded credentials
5. `claude-plugin/.mcp.json` — verify no secrets in MCP config
6. `claude-plugin/.claude-plugin/plugin.json` — verify no credentials in plugin manifest
7. Docker/CI configs — verify no secrets in build args, workflow files, or image layers

**If you find a secret:** STOP. Do not commit it, do not include it in any output.

### Severity Classification
- **CRITICAL**: OAuth tokens in code/logs, API keys in source, secrets in tool responses, credentials in plugin manifests
- **HIGH**: Missing input validation on MCP tool parameters, secrets in Docker layers, unsanitized DSL queries
- **MEDIUM**: Verbose error messages exposing internal infrastructure, missing rate limiting on MCP endpoints, overly permissive CORS
- **LOW**: Missing request logging, inconsistent error response formats, missing security headers
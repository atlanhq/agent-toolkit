# Atlan MCP CLI — Implementation Plan

> **Status:** P0 in progress. P1/P2 deferred to future PRs.
> **Approach:** Lighter-touch — keep the generated single-file CLI working, extract only auth/runtime seams; defer package-layout churn to P1.

---

## 0. Verified facts (Apr 2026)

- **`mcp.atlan.com` proxy is already deployed** with refresh-token support:
  - `GET /.well-known/oauth-authorization-server` → `grant_types_supported: ["authorization_code", "refresh_token"]`
  - `POST /oauth/token` accepts both grants and decodes the refresh-token JWT to derive tenant (`oauth_proxy/app.py:219`)
  - `POST /oauth/register` returns static `client_id=mcp-client`, `client_secret=placeholder`
- **Refresh tokens carry tenant info** in their `iss` JWT claim — the CLI never needs to persist tenant URL for OAuth.
- The current generated CLI uses `cyclopts` + `fastmcp.Client` and works against `https://atlan-demo.atlan.com/mcp` (verified end-to-end with the OAuth flow).

---

## 1. End-state UX

```bash
# One-time setup
atlan login                                       # interactive: pick OAuth or API key
atlan login --oauth                               # force OAuth, non-interactive
atlan login --api-key sk-xxx --tenant https://demo.atlan.com   # api-key mode

# Daily use — no flags, no env vars
atlan semantic_search_tool --user-query "PII tables"
atlan list-tools
atlan get_asset_tool --guid abc-123

# Diagnostics
atlan status                                      # auth mode, tenant, expiry
atlan logout                                      # wipe everything

# Per-call overrides (still supported)
atlan --oauth semantic_search_tool ...            # force fresh OAuth this call
atlan --api-key sk-xxx --tenant https://t.com ... # one-shot API key
```

**Exit codes:**
| Code | Meaning |
|------|---------|
| 0 | success |
| 1 | server/tool returned error |
| 2 | auth required or refresh failed → `atlan login` |
| 3 | config / invocation error |

---

## 2. Approach

**Keep the file shape for P0.** The generated `atlan_cli.py` stays a single file; we only add handwritten helpers for auth, config, and IO. No `src/atlan_cli/` rewrite until UX is validated. This minimizes risk and preserves the regeneration story.

**Stay with `cyclopts`.** Already working, type-hint native, async-friendly. For prettier output we add `rich` (already a dep) panels/tables and `questionary` for interactive `atlan login` prompts. No need to switch to click/typer.

**Use the existing keychain library** (`keyring`) — already a dep. JSON-file fallback only when keychain unavailable.

---

## 3. Architecture

### 3.1 Storage layout

| Path | Contents | Permissions |
|------|----------|-------------|
| `~/.atlan/config.json` | `{"auth_mode": "oauth"\|"api-key", "tenant": "..." (api-key only), "client_id": "mcp-client"}` | 0600 |
| OS keyring `atlan-mcp/refresh_token` | Long-lived JWT (~30d) | OS-level |
| OS keyring `atlan-mcp/access_token` | Short-lived JWT JSON `{"access_token", "expires_at"}` | OS-level |
| OS keyring `atlan-mcp/api_key` | Atlan API key (api-key mode only) | OS-level |
| `~/.atlan/credentials.json` (fallback) | Same secrets, used only when `keyring` raises | 0600 |

### 3.2 Auth resolution

```
                 ┌── --api-key override?  → BearerAuth(key) → {tenant}/mcp/api-key
                 │
resolve_auth() ──┼── --oauth override?    → fresh browser flow → BearerAuth(token)
                 │                          (don't persist by default)
                 │
                 └── persisted config?
                       ├── api-key: read api_key from keyring → BearerAuth → {tenant}/mcp/api-key
                       └── oauth:
                             ├── access cached & valid → BearerAuth → mcp.atlan.com/mcp
                             ├── refresh OK → store new tokens → BearerAuth
                             └── refresh failed → wipe creds → exit 2
```

### 3.3 Stale-cache wipe invariant

`wipe_credentials()` is called from exactly **three places**:
1. Refresh fails (`invalid_grant` or HTTP error) — server says token revoked.
2. `atlan logout`.
3. `atlan login` (always wipes before writing — prevents mode-switch cross-contamination).

Any other call to wipe is a bug. Transient network errors must not wipe credentials.

### 3.4 Refresh-token grant

```
POST https://mcp.atlan.com/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&refresh_token=<jwt>
&client_id=mcp-client
&client_secret=placeholder
```

Response:
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<rotated-jwt>",
  "expires_in": 300,
  "token_type": "Bearer"
}
```

Store new access token with `expires_at = now + expires_in - 30` (30s safety margin). If response includes a new refresh token (rotation), replace the stored one.

---

## 4. P0 — Demo-ready (this PR)

| # | Item | File | Status |
|---|------|------|--------|
| 1 | Hardcode `https://mcp.atlan.com` as default OAuth proxy URL | `atlan_cli.py` | ⏳ |
| 2 | `~/.atlan/config.json` reader/writer | `atlan_cli.py` | ⏳ |
| 3 | Keyring secret store with file fallback | `atlan_cli.py` | ⏳ |
| 4 | `_resolve_auth()` rewrite with override → config → refresh hierarchy | `atlan_cli.py` | ⏳ |
| 5 | `atlan login` (interactive + `--oauth` + `--api-key --tenant`) | `atlan_cli.py` | ⏳ |
| 6 | `atlan logout` | `atlan_cli.py` | ⏳ |
| 7 | `atlan status` | `atlan_cli.py` | ⏳ |
| 8 | Refresh-token grant + stale-cache wipe | `atlan_cli.py` | ⏳ |
| 9 | Move `--oauth` / `--api-key` / `--tenant` / `--json` to global flags in `main()` | `atlan_cli.py` | ⏳ |
| 10 | Exit codes 0/1/2/3 | `atlan_cli.py` | ⏳ |
| 11 | `--json` raw output mode | `atlan_cli.py` | ⏳ |
| 12 | `.gitignore` build artifacts; drop tracked `.env`/`.venv`/`uv.lock` | `.gitignore` | ⏳ |
| 13 | Update README to login-first UX | `README.md` | ⏳ |

---

## 5. P1 — Packaging & polish (next sprint)

- `version.txt` + dynamic version from `importlib.metadata`
- `.github/workflows/mcp-cli-publish.yaml` modeled on `pyatlan-publish.yaml`
- Reserve PyPI name `atlan-cli` (fallback: `atlan-mcp-cli`)
- `uv tool install atlan-cli` — frictionless install for any agent author
- Cyclopts command groups for categorized `--help` (Search / Update / Glossary / DQ / CM / Tags)
- `rich` tables for `list-tools`, syntax-highlighted JSON for tool results
- `questionary` for prettier interactive `atlan login` prompts

---

## 6. P2 — Maintenance & nice-to-haves

- Separate generated commands from auth/runtime via `_generated.py` import + `Makefile regenerate` target with merge script
- Document the regeneration workflow without breaking auth glue
- `atlan list-tools --category glossary` filtering
- Multi-tenant `~/.atlan/profiles/<name>.json` + `atlan --profile <name>`
- Mid-stream token refresh for long-running batches (today refresh only happens at request-start boundary)
- Headless device-flow when `DISPLAY` not set
- `atlan completion zsh|bash|fish`

---

## 7. Public interfaces

**Commands**
- `atlan login [--oauth | --api-key <key> [--tenant <url>]]`
- `atlan logout`
- `atlan status`
- `atlan list-tools`, `atlan list-resources`, `atlan list-prompts`, `atlan read-resource`, `atlan get-prompt`
- `atlan <tool_name> [tool args]` for every MCP tool

**Global flags** (consumed in `main()` before cyclopts):
- `--oauth` — force fresh OAuth this invocation
- `--api-key <key>` — one-shot API key (requires `--tenant`)
- `--tenant <url>` — tenant URL for one-shot api-key mode
- `--json` — emit raw JSON to stdout, all logs to stderr

**Config file shape** (`~/.atlan/config.json`):
```json
{
  "auth_mode": "oauth",
  "client_id": "mcp-client"
}
```
or
```json
{
  "auth_mode": "api-key",
  "tenant": "https://demo.atlan.com"
}
```

**Secrets**
- Never written to repo files, `.env.example`, logs, or world-readable local files.
- Keyring service name: `atlan-mcp`, account names: `refresh_token`, `access_token`, `api_key`.

---

## 8. Test plan (P0)

| Scenario | Expected |
|----------|----------|
| First `atlan login` (OAuth) | Browser opens, callback succeeds, refresh+access tokens in keyring, config written |
| `atlan semantic_search_tool` after login | Works without flags, uses cached access token |
| Access token expired, refresh succeeds | Tool call works, tokens rotated in keyring |
| Refresh token revoked (manual test) | Exit 2, tokens wiped, config retained, message "run atlan login" |
| `atlan login --api-key sk-x --tenant https://t.com` | Validates against `/api/meta/whoami` (or similar), persists |
| `atlan list-tools` in api-key mode | Works without browser |
| `atlan logout` | Wipes config + all keyring entries |
| Per-call `atlan --oauth …` after logout | Works one-shot, does not persist |
| `atlan --api-key sk-x --tenant https://t.com semantic_search_tool …` after logout | Works one-shot, does not persist |
| `atlan status` unauthenticated | Exit 2, single line: "Not authenticated. Run `atlan login`." |
| `atlan status` authenticated | Exit 0, mode + tenant + expiry |
| `--json` flag | Raw JSON to stdout for both success and error |
| Malformed `~/.atlan/config.json` | Exit 3 with clear message |
| Keyring unavailable | Falls back to `~/.atlan/credentials.json` (0600) |

---

## 9. Assumptions

- `mcp.atlan.com/oauth/token` continues to support `refresh_token` grant.
- The refresh token JWT continues to encode tenant in the `iss` claim (verified against `oauth_proxy/app.py:219`).
- For api-key validation, we use `{tenant}/api/meta/whoami` — to be confirmed; fall back to attempting an MCP `initialize` if `/api/meta/whoami` is not available.
- The generated tool functions in `atlan_cli.py` are the source of truth for tool argument surfaces in P0.

---

## 10. References

- Proxy implementation: `agent-toolkit-internal:mcp_proxy:oauth_proxy/app.py` (token endpoint at line 608, refresh handling at 646, JWT issuer extraction at 219)
- Live proxy (verified Apr 28): `https://mcp.atlan.com/.well-known/oauth-authorization-server`, `/oauth/token`, `/oauth/register`
- Pyatlan packaging template: `atlan-python:pyproject.toml`, `.github/workflows/pyatlan-publish.yaml`
- Current CLI: `agent-toolkit:feat/mcp-cli:mcp-cli/atlan_cli.py`

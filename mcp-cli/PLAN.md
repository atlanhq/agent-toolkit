# Atlan MCP CLI — Improvement Plan

Based on the meeting discussion (Abhinav, Ankit, Hrushikesh) and a review of how `pyatlan` is packaged.

## Goals

| Goal | What it means |
|------|---------------|
| **One-command install** | `uv tool install atlan-mcp-cli` (PyPI), no clone-and-install dance |
| **No `--oauth` repetition** | `atlan login` once → all subsequent calls authenticated automatically |
| **No URL configuration** | Default endpoint hardcoded to `https://mcp.atlan.com/mcp` (proxy) |
| **Agent-friendly diagnostics** | `atlan status` returns clear "ready" vs. "missing X" so agents can self-correct |
| **Zero-edit schema sync** | Regenerating against new MCP schema is a single make target, not manual paste |

## What changes (in priority order)

### 1. `atlan login` / `atlan logout` / `atlan status`

Replace the `--oauth` flag with persistent login state.

```bash
atlan login                  # interactive: prompts for OAuth (default) or API key
atlan login --oauth          # force OAuth, non-interactive
atlan login --api-key <k>    # set API key non-interactively (for agents/CI)
atlan logout                 # clear stored credentials and tokens
atlan status                 # diagnostic: prints auth state + tenant + token expiry
```

**Behavior:**
- `login` writes auth mode to `~/.atlan/config.json` (`{"auth": "oauth"}` or `{"auth": "api-key"}`).
- For OAuth, opens browser and stores token in OS keychain (existing flow).
- For API key, stores in keychain with service `atlan-cli/api-key`.
- `status` returns:
  - ✅ `Ready — authenticated as <user> via <oauth|api-key>, expires in <duration>`
  - ❌ `Not authenticated — run 'atlan login' to set up`
  - ❌ `Token expired — run 'atlan login' to refresh` (with exit code 2 so agents detect it)
- All tool calls auto-route based on stored auth — no `--oauth` flag needed at call time.

### 2. Hardcode the proxy endpoint

```python
DEFAULT_BASE_URL = "https://mcp.atlan.com"
```

- Drop the requirement to set `ATLAN_BASE_URL` in normal use.
- Keep `ATLAN_BASE_URL` env-var override for staging/dev tenants only (documented but not surfaced).
- Tenant identity comes from the OAuth token (issuer claim) or API key (decoded), not from a user-supplied URL.

### 3. `~/.atlan/` config directory

Mirror the `~/.claude/` and `~/.cursor/` pattern for inspectability.

```
~/.atlan/
├── config.json          # {"auth": "oauth", "default_tenant": "..."}
└── logs/                # optional: tool call audit log (off by default)
```

- Tokens stay in OS keychain (Mac Keychain, Windows Credential Manager, Linux Secret Service via `keyring`).
- Fallback `~/.atlan/credentials.json` (chmod 600) for systems without a keychain (CI, headless Linux).
- Easy to inspect when debugging customer issues — Hrushikesh's point about `claude_desktop_config.json` style.

### 4. PyPI distribution (`uv tool install atlan-mcp-cli`)

Modeled on pyatlan's pipeline.

**Steps:**
1. Add `pyatlan-style` `pyproject.toml` with proper metadata (authors, classifiers, urls, license).
2. Use dynamic version from a `version.txt` file in the package.
3. Add `.github/workflows/mcp-cli-publish.yaml` triggered on `release: published` for tags matching `mcp-cli-v*`.
   - Uses `astral-sh/setup-uv@v7`, runs `uv build` + `uv publish` with `PYPI_API_TOKEN`.
4. Reserve the package name `atlan-mcp-cli` on PyPI.
5. Final user experience:
   ```bash
   uv tool install atlan-mcp-cli
   atlan login
   atlan semantic_search_tool --user-query "PII tables"
   ```

### 5. Agent-friendly output mode

- Default human output: rich tables / formatted JSON.
- `--json` flag (or `ATLAN_OUTPUT=json` env var): emits raw JSON to stdout, all logs to stderr — clean for agent parsing.
- Exit codes:
  - `0` success
  - `1` tool error (server returned an error)
  - `2` auth error (run `atlan login`)
  - `3` config / validation error
- Optionally write last result to `~/.atlan/last_result.json` for resumability (Hrushikesh's "temp file" idea — opt-in via `--save-last`).

### 6. Schema regeneration via Makefile

Currently the README has a manual paste step. Replace with:

```makefile
regenerate:
	fastmcp generate-cli https://mcp.atlan.com/mcp --auth oauth --output _generated.py --force
	python _merge_auth.py _generated.py atlan_cli.py   # script that re-applies our auth/main block
	rm _generated.py
```

A small `_merge_auth.py` script keeps the top-of-file block (imports, auth, `_resolve_auth`, `_client`, `main`) intact while replacing the tool-command section. Removes the "remember to paste auth back" footgun.

### 7. Beautified CLI surface

- Group commands in `--help` output by category (Search, Update, Glossary, DQ, etc.) using cyclopts groups.
- Add brief examples in each tool's help text (one-liner showing typical usage).
- Color/icon polish using `rich` (already a dep): green for success, red for errors, dim for metadata.
- For `list-tools`, add a `--category` filter (e.g., `atlan list-tools --category glossary`).

### 8. Validation / preflight

`atlan status` runs a real ping:
1. Reads config + credentials.
2. Hits `mcp.atlan.com/mcp` `initialize` to confirm the token is valid.
3. Reports tenant, user, token expiry, and which auth mode was used.
4. If anything fails, prints exactly which step failed and the fix.

### 9. Cleanups (current PR carryovers)

- Stop tracking `atlan-claude-plugin.tar.gz` and `.zip` build artifacts (add to `.gitignore`).
- Remove `mcp-cli/.env`, `mcp-cli/.venv`, `mcp-cli/build/`, `mcp-cli/atlan_mcp_cli.egg-info/`, `mcp-cli/uv.lock` from git — these are local artifacts from `uv tool install`.

## Out of scope (for now)

- A separate "atlan agent toolkit" higher-level wrapper — the CLI stays a thin transport over MCP, agents handle reasoning.
- Renaming MCP tools — they keep their server-side names. If we want shorter names, change them in MCP first, then regenerate.
- Beautifying the OAuth callback page (the FastMCP default page) — not blocking; can be polished later when we move to atlanhq-branded callback HTML.

## Phasing

| Phase | Items | Why first |
|-------|-------|-----------|
| **P0 (Activate demo)** | 1 (`login`/`status`), 2 (hardcoded proxy), 3 (`~/.atlan/`), 7 (basic polish), 9 (cleanups) | Demo tonight needs `atlan login` → tool calls to "just work" |
| **P1 (next sprint)** | 4 (PyPI publish), 5 (`--json` flag), 8 (real preflight) | Once we've validated the UX, ship to PyPI so any agent author can `uv tool install atlan-mcp-cli` |
| **P2** | 6 (Makefile regen), `--category` filtering, error message polish | Maintenance layer — once the core is shipped |

## Open questions

- **Package name on PyPI**: `atlan-mcp-cli`, `atlan-cli`, or `atlan`? `atlan` may collide with future official Atlan CLI; `atlan-mcp-cli` is most explicit but verbose. Recommend `atlan-cli` and own the namespace.
- **Token refresh**: do we silently refresh on expiry, or always require explicit `atlan login`? The OAuth provider supports refresh tokens — let's silently refresh and only prompt if the refresh token itself is invalid.
- **Multi-tenant**: does an end-user need to support multiple tenants (`atlan login --tenant prod`, `atlan --tenant prod search …`)? Not in the demo, but worth designing the config schema to allow it.

## References

- pyatlan packaging: `/Users/abhinav.mathur/atlan-repos/atlan-python/pyproject.toml`, `pyatlan-publish.yaml`
- Current CLI: `/Users/abhinav.mathur/atlan-repos/agent-toolkit/mcp-cli/atlan_cli.py` (branch `feat/mcp-cli`)
- Meeting transcript with Ankit, Hrushikesh, Abhinav

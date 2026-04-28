# Atlan MCP CLI — Detailed Implementation Plan

Based on the meeting with Ankit & Hrushikesh, a review of `pyatlan` packaging, and the `mcp_proxy` branch on `agent-toolkit-internal`.

---

## 0. Key insight from the `mcp_proxy` branch

The `oauth_proxy/app.py` on `agent-toolkit-internal:mcp_proxy` already implements the proxy at `mcp.atlan.com/oauth/*`:

| Endpoint | Purpose | Notes |
|----------|---------|-------|
| `GET /.well-known/oauth-authorization-server` | OASM discovery | Advertises `grant_types_supported: ["authorization_code", "refresh_token"]` |
| `POST /oauth/register` | Dynamic Client Registration | Returns `client_id=mcp-client`, `client_secret=placeholder` |
| `POST /oauth/token` | Token endpoint | Handles **both** `authorization_code` AND `refresh_token` grants |

The `extract_tenant_from_refresh_token()` function (line 219) decodes the refresh token JWT and reads the `iss` claim → tenant is fully encoded in the refresh token, so **the CLI never needs to know which tenant it talks to** beyond initial login.

**This means:**
- We can store **only the refresh token** in the keyring (long-lived, ~30 days).
- Each command gets a fresh access token via the refresh grant, with no browser interaction.
- The tenant URL never appears in our config — the proxy handles it.

---

## 1. End-state UX

```bash
# One-time setup (interactive prompt picks oauth or api-key)
atlan login

# Or non-interactively
atlan login --oauth
atlan login --api-key sk-xxx
atlan login --api-key sk-xxx --tenant https://demo.atlan.com   # api-key only

# Daily use — no flags needed
atlan semantic_search_tool --user-query "PII tables"
atlan list-tools
atlan get_asset_tool --guid abc-123

# Diagnostics
atlan status      # who am I, mode, expiry, tenant
atlan logout      # wipe everything

# Power-user overrides (still supported)
atlan --oauth semantic_search_tool ...     # force fresh OAuth this call
atlan --api-key sk-xxx semantic_search_tool ...   # one-shot api key
```

Exit codes (agent-friendly):
- `0` success
- `1` server returned a tool error
- `2` not authenticated / token expired and refresh failed → `atlan login`
- `3` config error (invalid api-key shape, missing tenant for api-key, etc.)

---

## 2. CLI Library Decision

**Stay with `cyclopts`** — switching mid-stream is churn for marginal gain.

| Library | Pros | Cons | Verdict |
|---------|------|------|---------|
| **cyclopts** (current) | Type-hint first, native async, already wired up, `rich`-powered help | Less mindshare than click | **Keep** — meets every requirement |
| typer | Big ecosystem | Click underneath; sync-only ergonomics for async commands | No upside for our case |
| click | Battle-tested | Verbose decorators, pre-typing era | Step backwards |
| rich-click | Pretty click | Locked into click | Same downsides as click |

**What we add for "prettier" without switching libraries:**
- `rich.console.Console` (already imported) for tables, panels, syntax-highlighted JSON
- `rich.progress` for long tool calls
- `questionary` for `atlan login` interactive prompt (`Choose auth method ▸`)
- Cyclopts command groups for category-grouped help (Search / Update / Glossary / DQ)

---

## 3. Architecture

### 3.1 File layout

```
mcp-cli/
├── pyproject.toml                # PyPI metadata, dynamic version from version.txt
├── version.txt                   # single source of truth for version
├── README.md
├── PLAN.md                       # this file (drop after rollout)
├── Makefile                      # regenerate, build, publish targets
├── src/
│   └── atlan_cli/
│       ├── __init__.py           # __version__ from importlib.metadata
│       ├── __main__.py           # python -m atlan_cli
│       ├── app.py                # cyclopts.App + main() entry
│       ├── auth/
│       │   ├── __init__.py
│       │   ├── config.py         # ~/.atlan/config.json read/write
│       │   ├── keyring_store.py  # access/refresh token storage in OS keychain
│       │   ├── oauth.py          # browser flow + refresh-token reuse
│       │   ├── api_key.py        # api-key validation/storage
│       │   └── resolver.py       # `_resolve_auth()` — picks mode, refreshes if needed
│       ├── commands/
│       │   ├── login.py          # atlan login / logout / status
│       │   └── tools/
│       │       └── _generated.py # output of `fastmcp generate-cli` — tool commands
│       ├── transport.py          # Client(...) wrapper, exit-code mapping
│       └── output.py             # rich formatters, --json mode, exit codes
├── scripts/
│   └── merge_generated.py        # post-process fastmcp's output, re-apply our top block
└── .github/workflows/
    └── mcp-cli-publish.yaml      # PyPI publish on tag mcp-cli-v*
```

### 3.2 Config / credentials storage

| File | Contents | Permissions |
|------|----------|-------------|
| `~/.atlan/config.json` | `{"auth_mode": "oauth"\|"api-key", "tenant": "https://..." (api-key only), "client_id": "mcp-client"}` | 0644 |
| OS keyring `atlan-mcp/access_token` | Short-lived JWT (5–60 min) | keychain |
| OS keyring `atlan-mcp/refresh_token` | Long-lived JWT (~30 days) | keychain |
| OS keyring `atlan-mcp/api_key` | Atlan API key (only when in api-key mode) | keychain |
| `~/.atlan/credentials.json` (fallback for headless) | `{"refresh_token": "...", "access_token": "...", "expires_at": <ts>}` | **0600** |

Resolution order on each command:
1. Read `~/.atlan/config.json` → know which mode.
2. **api-key mode**: pull api-key from keyring → done.
3. **oauth mode**:
    - Pull access_token. If `now + 30s < expires_at`, use it.
    - Else pull refresh_token, hit `https://mcp.atlan.com/oauth/token` with `grant_type=refresh_token`, get new access+refresh, store both.
    - If refresh fails → wipe keyring entries (stale cache cleanup) and exit `2` with "Session expired — run `atlan login`".

### 3.3 Auth resolver pseudo-code

```python
@dataclass
class ResolvedAuth:
    client_spec: str             # full MCP URL
    auth: httpx.Auth             # BearerAuth or pre-fetched Bearer
    mode: Literal["oauth", "api-key"]

async def resolve_auth(*, force_oauth: bool = False, override_api_key: str | None = None) -> ResolvedAuth:
    # 1. Per-call overrides win
    if override_api_key:
        return ResolvedAuth(MCP_URL_API_KEY, BearerAuth(override_api_key), "api-key")
    if force_oauth:
        return await _do_full_oauth_login(persist=False)

    # 2. Read persisted config
    cfg = load_config()
    if cfg is None:
        raise NotAuthenticated("Run `atlan login` to set up credentials")

    if cfg.auth_mode == "api-key":
        api_key = keyring.get("atlan-mcp", "api_key")
        if not api_key:
            wipe_credentials()
            raise NotAuthenticated("API key missing from keychain — run `atlan login`")
        return ResolvedAuth(f"{cfg.tenant}/mcp/api-key", BearerAuth(api_key), "api-key")

    # oauth mode
    access = keyring.get("atlan-mcp", "access_token_json")
    if access and not _expired(access):
        return ResolvedAuth(MCP_URL, BearerAuth(access["access_token"]), "oauth")

    # Refresh
    refresh = keyring.get("atlan-mcp", "refresh_token")
    if not refresh:
        wipe_credentials()
        raise NotAuthenticated("No refresh token — run `atlan login`")
    try:
        new = await _refresh(refresh)            # POST mcp.atlan.com/oauth/token
        keyring.set("atlan-mcp", "access_token_json", new)
        if new.get("refresh_token"):              # refresh-token rotation
            keyring.set("atlan-mcp", "refresh_token", new["refresh_token"])
        return ResolvedAuth(MCP_URL, BearerAuth(new["access_token"]), "oauth")
    except RefreshFailed:
        wipe_credentials()                        # mandatory stale-cache wipe
        raise NotAuthenticated("Session expired — run `atlan login`")
```

### 3.4 `atlan login` flow

```
$ atlan login
? How do you want to authenticate?
  ▸ OAuth (browser)
    API key
[OAuth selected]
✓ Opening browser…
  → https://atlan-demo.atlan.com/auth/realms/default/protocol/openid-connect/auth?…
✓ Token received and stored in OS keychain.
✓ You are logged in as abhinav.mathur@atlan.com
  Tenant: atlan-demo.atlan.com
  Token expires in: 5m (auto-refresh enabled)
```

For api-key:

```
$ atlan login --api-key sk-xxx
? Tenant URL: https://atlan-demo.atlan.com
✓ Validated key against /api/auth/whoami → user: abhinav.mathur
✓ Stored in OS keychain.
```

`atlan logout` deletes config.json + all keyring entries.

`atlan status`:
```
✓ Authenticated via OAuth
  User: abhinav.mathur@atlan.com
  Tenant: atlan-demo.atlan.com
  Access token expires in: 8m 32s (auto-refresh on next call)
  Refresh token expires in: 29d 17h
```

When unauthenticated, status exits `2` with a single-line "Not authenticated. Run `atlan login`." — agents read stdout and act.

---

## 4. Phasing

### **P0 — Activate demo-ready (today + tonight)**

| # | Item | Files touched | Effort |
|---|------|---------------|--------|
| 1 | Hardcode proxy URL as default (`https://mcp.atlan.com/mcp`) | `atlan_cli.py` | 10 min |
| 2 | Migrate to `~/.atlan/config.json` for auth mode + `keyring` for tokens | new `auth/` module | 1.5 h |
| 3 | `atlan login` (interactive + `--oauth` + `--api-key`) | `commands/login.py` | 2 h |
| 4 | `atlan logout`, `atlan status` | `commands/login.py` | 30 min |
| 5 | Auto-refresh access token via refresh-token grant; wipe on failure | `auth/oauth.py` | 1 h |
| 6 | Drop `--oauth` requirement from per-tool calls — flag becomes per-call override | `app.py`, `transport.py` | 30 min |
| 7 | Cleanups: `.gitignore` build artifacts, drop tracked `.env`, `.venv`, `uv.lock` from git | `.gitignore`, `git rm --cached` | 15 min |
| 8 | Preserve current `pyproject.toml` (entry point `atlan = atlan_cli.app:main`) | `pyproject.toml` | 10 min |

P0 deliverable:

```bash
uv tool install /path/to/agent-toolkit/mcp-cli
atlan login                                 # browser opens, log in once
atlan semantic_search_tool --user-query x   # works, no flags, no env vars
atlan status                                # shows auth state
```

### **P1 — Polish + PyPI (next sprint)**

| # | Item | Files | Effort |
|---|------|-------|--------|
| 9 | Pretty output: rich tables for `list-tools`, syntax-highlighted JSON for tool results | `output.py` | 2 h |
| 10 | `--json` flag + `ATLAN_OUTPUT=json` for clean agent parsing | `output.py`, all commands | 1 h |
| 11 | `--save-last` writes `~/.atlan/last_result.json` (Hrushikesh's idea — opt-in) | `output.py` | 30 min |
| 12 | Cyclopts groups in `--help` (Search / Update / Glossary / DQ / Custom Metadata / Tags) | `app.py` | 1 h |
| 13 | `version.txt` + dynamic version + `__version__` exposed | `pyproject.toml`, `__init__.py` | 30 min |
| 14 | GitHub Actions publish workflow (`.github/workflows/mcp-cli-publish.yaml`) — modeled exactly on `pyatlan-publish.yaml` | new file | 1 h |
| 15 | Reserve `atlan-cli` on PyPI; first release | release process | 30 min |
| 16 | `atlan login --api-key` validates against `/api/meta/whoami` before storing | `auth/api_key.py` | 30 min |

P1 deliverable: `uv tool install atlan-cli` from PyPI works for any agent author.

### **P2 — Maintenance + nice-to-haves**

| # | Item | Files | Effort |
|---|------|-------|--------|
| 17 | `Makefile` target for `regenerate` (fastmcp generate-cli + merge script) | `Makefile`, `scripts/merge_generated.py` | 2 h |
| 18 | `atlan list-tools --category glossary` filtering | `commands/tools/list_tools.py` | 30 min |
| 19 | Structured error messages — distinguish auth, network, schema, server | `transport.py` | 1 h |
| 20 | `atlan login --tenant <url>` for multi-tenant config (`~/.atlan/profiles/<name>.json`); `atlan --profile <name> ...` | `auth/config.py` | 3 h |
| 21 | Token refresh attempted **inside** the request flow (not just on each call boundary) — handles long-running batch where token expires mid-loop | `transport.py` | 1 h |
| 22 | Headless mode: print device-flow URL + code instead of opening browser when `DISPLAY` not set | `auth/oauth.py` | 1 h |
| 23 | `atlan completion zsh|bash|fish` for shell tab-completion | `commands/completion.py` | 1 h |
| 24 | Telemetry opt-in (`atlan login --telemetry on`) — count tool calls, errors, latency | `output.py` | 2 h |

---

## 5. Detailed implementation notes

### 5.1 Refresh-token flow (P0 #5)

```python
import httpx, time

PROXY_TOKEN_ENDPOINT = "https://mcp.atlan.com/oauth/token"

async def _refresh(refresh_token: str) -> dict:
    """Exchange refresh token for new access+refresh.

    Server (mcp_proxy/app.py:646) decodes the refresh token, derives the
    tenant from its `iss` claim, and forwards to that tenant's Keycloak.
    Returns: {access_token, refresh_token, expires_in, token_type, ...}
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            PROXY_TOKEN_ENDPOINT,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": "mcp-client",
                "client_secret": "placeholder",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if resp.status_code != 200:
        raise RefreshFailed(f"{resp.status_code}: {resp.text[:200]}")
    body = resp.json()
    body["expires_at"] = int(time.time()) + body.get("expires_in", 300) - 30  # 30s safety
    return body
```

Storing the result:
- Store `{"access_token": ..., "expires_at": ts}` JSON-encoded under `atlan-mcp/access_token_json`.
- Store the (possibly rotated) refresh token under `atlan-mcp/refresh_token`.
- On `RefreshFailed`, call `wipe_credentials()` immediately so the next call starts fresh — this is the "always remove stale cache" requirement.

### 5.2 Stale cache invariant (P0 #5)

`wipe_credentials()` is called from exactly three places:
1. Refresh fails (server says `invalid_grant` → refresh token revoked).
2. `atlan logout`.
3. `atlan login` (always wipes before writing new state — prevents mode-switch cross-contamination).

Never call `wipe_credentials()` from any other path; otherwise `atlan login` followed by transient network failures could surprise the user with re-prompt loops.

### 5.3 `--oauth` and `--api-key` as overrides (P0 #6)

Make them root-level cyclopts parameters (not subcommand args). Cyclopts allows global flags via `app.meta.command()`:

```python
app = cyclopts.App(name="atlan", help="Atlan MCP CLI")

# Global override flags consumed in main() before cyclopts parses subcommand
def main() -> None:
    args = sys.argv[1:]
    overrides = {}
    if "--oauth" in args:
        args.remove("--oauth")
        overrides["force_oauth"] = True
    for i, a in enumerate(args):
        if a == "--api-key":
            overrides["api_key"] = args[i + 1]
            del args[i:i + 2]
            break
        if a.startswith("--api-key="):
            overrides["api_key"] = a.split("=", 1)[1]
            del args[i]
            break
    set_overrides(overrides)            # module-level, picked up by resolve_auth
    sys.argv[1:] = args
    app()
```

This keeps the per-call override functional without polluting every tool's signature.

### 5.4 Pretty output (P1 #9)

```python
from rich.table import Table
from rich.syntax import Syntax
from rich.console import Console

console = Console()

def render_tool_result(content) -> None:
    if _is_json(content):
        if OUTPUT_MODE == "json":
            print(json.dumps(content))           # raw, agent-friendly
            return
        console.print(Syntax(json.dumps(content, indent=2), "json", theme="monokai"))
    else:
        console.print(content)
```

For `list-tools`:

```python
table = Table(title="Atlan MCP Tools", show_lines=True)
table.add_column("Category", style="cyan")
table.add_column("Tool")
table.add_column("Description", overflow="fold")
for tool in tools:
    table.add_row(_categorize(tool.name), tool.name, tool.description)
console.print(table)
```

### 5.5 Cleanups (P0 #7)

`.gitignore` additions:
```
mcp-cli/.env
mcp-cli/.venv/
mcp-cli/build/
mcp-cli/dist/
mcp-cli/*.egg-info/
mcp-cli/uv.lock          # debatable — pyatlan tracks it; for a tool, prefer not
*.tar.gz
*.zip
```

`git rm --cached`:
```
mcp-cli/.env
mcp-cli/uv.lock
mcp-cli/atlan_mcp_cli.egg-info/
mcp-cli/build/
atlan-claude-plugin.tar.gz
atlan-claude-plugin.zip
```

### 5.6 Schema regeneration (P2 #17)

`scripts/merge_generated.py`:
1. Reads our `commands/tools/_generated.py` to find the line `# === GENERATED TOOL COMMANDS BELOW ===`.
2. Reads fresh fastmcp output, finds the same marker.
3. Replaces everything below the marker, preserves everything above.

`Makefile`:
```makefile
.PHONY: regenerate build publish test

regenerate:
	fastmcp generate-cli https://mcp.atlan.com/mcp --auth oauth --output /tmp/atlan_generated.py --force
	python scripts/merge_generated.py /tmp/atlan_generated.py src/atlan_cli/commands/tools/_generated.py
	rm /tmp/atlan_generated.py

build:
	uv build

publish: build
	uv publish

test:
	pytest tests/
```

### 5.7 GitHub Actions publish workflow (P1 #14)

Lifted directly from `atlan-python/.github/workflows/pyatlan-publish.yaml`:

```yaml
name: Publish atlan-cli to PyPI
on:
  release:
    types: [published]
  workflow_dispatch:

jobs:
  deploy:
    if: success() && startsWith(github.ref, 'refs/tags/mcp-cli-v')
    runs-on: ubuntu-latest
    permissions: { contents: read }
    defaults: { run: { working-directory: mcp-cli } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.10' }
      - uses: astral-sh/setup-uv@v7
      - run: uv sync --group dev
      - run: uv run python scripts/check_tag.py
      - env: { UV_PUBLISH_TOKEN: ${{ secrets.PYPI_API_TOKEN }} }
        run: |
          uv build
          uv publish
```

`scripts/check_tag.py` mirrors pyatlan's — refuses to publish if `version.txt` doesn't match the git tag.

### 5.8 Test plan

| Layer | Tests |
|-------|-------|
| `auth/resolver.py` | unit: api-key happy path, oauth happy path, expired access → refresh, refresh fail → wipe |
| `auth/keyring_store.py` | unit: round-trip, missing entry returns None |
| `auth/oauth.py` | mocked httpx — refresh request shape, browser flow stubbed |
| `commands/login.py` | integration: against a local fake proxy serving `/oauth/token` |
| `transport.py` | integration: real `mcp.atlan.com` with a test api-key (CI secret) |
| `output.py` | snapshot tests for rich rendering, --json mode |

---

## 6. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| PyPI name `atlan-cli` taken | Fall back to `atlan-mcp-cli`. Squat both for safety. |
| Refresh token revoked by Keycloak admin | Caught by `RefreshFailed` → wipe → user re-`login`. Already handled. |
| `mcp_proxy` branch not yet on prod `mcp.atlan.com` | Verify on Apr 30 cutover; until then, make `PROXY_BASE_URL` configurable (`ATLAN_PROXY_URL` env) for testing. |
| Keychain unavailable in headless Docker / CI | Fallback file `~/.atlan/credentials.json` chmod 600 — already in design. |
| User runs `atlan` and `atlan-cli` separately and gets confused | Single PyPI package, single entry point. |

---

## 7. References

- pyatlan packaging: `/Users/abhinav.mathur/atlan-repos/atlan-python/{pyproject.toml,check_tag.py,.github/workflows/pyatlan-publish.yaml}`
- MCP proxy refresh-token impl: `agent-toolkit-internal:mcp_proxy:oauth_proxy/app.py` (lines 219, 646–684)
- OAuth client lib: `mcp.client.auth.OAuthClientProvider` (mcp 1.27)
- Cyclopts docs: https://cyclopts.readthedocs.io/
- Meeting transcript: Ankit / Hrushikesh / Abhinav — paste in `mcp-cli/.notes/2026-04-28-meeting.md` if we want it tracked

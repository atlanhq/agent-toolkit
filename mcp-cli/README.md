# Atlan MCP CLI

A standalone CLI for calling Atlan MCP tools directly from your terminal — no IDE, no agent required.

## Installation

Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it, then install the CLI as a global tool:

```bash
uv tool install /path/to/agent-toolkit/mcp-cli
```

Add `~/.local/bin` to your PATH if prompted:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Quick Start

```bash
# One-time login — opens browser for OAuth
atlan login

# Or log in with an API key
atlan login --api-key sk-xxx --tenant https://your-tenant.atlan.com

# Check your auth status
atlan status

# Run tools — no flags needed after login
atlan semantic_search_tool --user-query "PII tables in Snowflake"
atlan list-tools
atlan get_asset_tool --guid "abc-123"
```

## Auth Commands

| Command | Description |
|---------|-------------|
| `atlan login` | OAuth browser login (default) |
| `atlan login --api-key KEY --tenant URL` | Log in with an API key |
| `atlan logout` | Remove stored credentials |
| `atlan status` | Show auth mode, tenant, and token expiry |

## Global Flags (per-call overrides)

These override stored credentials for a single invocation and are not persisted:

| Flag | Description |
|------|-------------|
| `--oauth` | Force fresh OAuth browser login this call |
| `--api-key KEY --tenant URL` | One-shot API key (not saved) |
| `--json` | Raw JSON to stdout; all logs go to stderr |

```bash
# One-shot overrides (no stored credentials needed)
atlan --oauth semantic_search_tool --user-query "PII tables"
atlan --api-key sk-xxx --tenant https://demo.atlan.com list-tools
atlan --json get_asset_tool --guid abc-123
```

## Available Tools

- **Search & discovery** — `semantic_search_tool`, `search_assets_tool`, `traverse_lineage_tool`
- **Asset detail** — `get_asset_tool`, `resolve_metadata_tool`
- **Asset updates** — `update_assets_tool`, `manage_announcements_tool`, `manage_asset_lifecycle_tool`
- **Glossary** — `create_glossaries`, `create_glossary_terms`, `create_glossary_categories`
- **Data governance** — `create_domains`, `create_data_products`
- **Data quality** — `create_dq_rules_tool`, `update_dq_rules_tool`, `schedule_dq_rules_tool`, `delete_dq_rules_tool`
- **Custom metadata** — `update_custom_metadata_tool`, `remove_custom_metadata_tool`, `create_custom_metadata_set_tool`
- **Tags** — `add_atlan_tags_tool`, `remove_atlan_tag_tool`

Run `atlan --help` to see all commands with their parameters.
Run `atlan list-tools` to see what the live MCP server exposes (requires auth).

## How Credentials Are Stored

| Storage | Contents |
|---------|----------|
| `~/.atlan/config.json` | Auth mode and tenant URL (no secrets) |
| OS keychain (`atlan-mcp`) | Access token, refresh token, or API key |
| `~/.atlan/credentials.json` | File fallback when OS keychain is unavailable |

OAuth access tokens auto-refresh via the `mcp.atlan.com` proxy — you rarely need to re-run `atlan login`.

## Updating

After pulling new changes:

```bash
uv tool install /path/to/agent-toolkit/mcp-cli --reinstall
```

## Regenerating the CLI

If tool schemas change (new tools added to the server), regenerate with:

```bash
fastmcp generate-cli https://your-tenant.atlan.com/mcp --auth oauth --output atlan_cli.py --force
```

Re-apply the auth/packaging block at the top after regeneration — `fastmcp` does not write auth into generated scripts.

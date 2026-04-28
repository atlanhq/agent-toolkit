# Atlan MCP CLI

A standalone CLI for calling Atlan MCP tools directly from your terminal — no IDE, no agent required.

## Installation

Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it, then install the CLI as a global tool:

```bash
uv tool install /path/to/agent-toolkit/mcp-cli
```

This gives you the `atlan` command globally. Add `~/.local/bin` to your PATH if prompted:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Configuration

Set your tenant URL and (optionally) an API key — either via environment variables or a `.env` file in the directory where you run `atlan`:

```bash
# .env
ATLAN_BASE_URL=https://your-tenant.atlan.com
ATLAN_API_KEY=your-api-key   # omit to use OAuth browser login
```

## Auth Modes

| Mode | How to activate | Endpoint used |
|------|----------------|---------------|
| **API key** | `ATLAN_BASE_URL` + `ATLAN_API_KEY` | `{base_url}/mcp/api-key` |
| **OAuth (PKCE)** | `ATLAN_BASE_URL` only, no `ATLAN_API_KEY` | `{base_url}/mcp` |
| **Force OAuth** | `--oauth` flag or `ATLAN_AUTH=oauth` | `{base_url}/mcp` |

OAuth tokens are cached in the OS keychain after the first browser login — subsequent runs skip the browser entirely.

The `--oauth` flag forces browser login even when `ATLAN_API_KEY` is set in `.env`.

## Usage

```bash
# Show all available commands
atlan --help

# List tools the MCP server exposes
atlan --oauth list-tools

# Search assets (OAuth)
atlan --oauth semantic_search_tool --user-query "PII tables in Snowflake"

# Search assets (API key — reads .env automatically)
atlan semantic_search_tool --user-query "PII tables in Snowflake"

# Traverse lineage
atlan --oauth traverse_lineage_tool --guid "abc-123" --direction DOWNSTREAM

# Get a specific asset
atlan --oauth get_asset_tool --guid "abc-123"
```

> **Note:** `--oauth` must come before the tool name (it's a global flag, not a tool argument).

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

Then re-apply the auth/packaging block at the top (everything above `app = cyclopts.App(...)`) — `fastmcp` does not write auth into generated scripts by design.

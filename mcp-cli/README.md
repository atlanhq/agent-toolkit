# Atlan MCP CLI

A standalone CLI for calling Atlan MCP tools directly from your terminal — no IDE, no agent required. Works on macOS, Windows, and Linux.

## Installation

Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it, then install the CLI as a global tool:

```bash
# From PyPI (once published)
uv tool install atlan-cli

# From source
uv tool install /path/to/agent-toolkit/mcp-cli
```

Add `~/.local/bin` to your PATH if prompted:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Quick Start

```bash
# One-time login — interactive: choose OAuth or API key
atlan login

# Or skip the prompt and log in directly
atlan login --oauth                                           # browser login
atlan login --api-key sk-xxx --tenant https://your-tenant.atlan.com  # API key

# Check your auth status
atlan status

# Run tools — no flags needed after login
atlan semantic_search_tool --user-query "PII tables in Snowflake"
atlan list-tools
atlan get_asset_tool --guid "abc-123"
```

`atlan login` with no flags shows an interactive prompt:

```
Choose login method:
  1  OAuth   — browser login via mcp.atlan.com
  2  API key — paste your Atlan API key

Choice [1/2] (1): 2
  API key: <paste key and press Enter>
  Tenant URL (e.g. https://demo.atlan.com): https://your-tenant.atlan.com
```

## Auth Commands

| Command | Description |
|---------|-------------|
| `atlan login` | Interactive: choose OAuth browser login or API key |
| `atlan login --oauth` | Force OAuth browser flow directly |
| `atlan login --api-key KEY --tenant URL` | Log in with an Atlan API key |
| `atlan logout` | Remove all stored credentials |
| `atlan status` | Show auth mode, tenant, and token expiry |

OAuth access tokens auto-refresh via the `mcp.atlan.com` proxy — you rarely need to re-run `atlan login`. To switch tenants, run `atlan logout` then `atlan login` again.

## Global Flags

These override stored credentials for a single invocation and are not persisted:

| Flag | Description |
|------|-------------|
| `--oauth` | Force fresh OAuth browser login this call |
| `--api-key KEY --tenant URL` | One-shot API key (not saved) |
| `--json` | Raw JSON to stdout; all logs go to stderr |

```bash
# One-shot overrides
atlan --oauth semantic_search_tool --user-query "PII tables"
atlan --api-key sk-xxx --tenant https://demo.atlan.com list-tools
atlan --json get_asset_tool --guid abc-123
```

## Available Tools

Run `atlan list-tools` to see the full list (requires auth). Common tools by category:

| Category | Tools |
|----------|-------|
| **Search & discovery** | `semantic_search_tool`, `search_assets_tool`, `search_atlan_docs_tool` |
| **Lineage** | `traverse_lineage_tool` |
| **Asset detail** | `get_asset_tool`, `resolve_metadata_tool`, `get_groups_tool` |
| **Asset updates** | `update_assets_tool`, `manage_announcements_tool`, `manage_asset_lifecycle_tool` |
| **Glossary** | `create_glossaries`, `create_glossary_terms`, `create_glossary_categories` |
| **Data mesh** | `create_domains`, `create_data_products` |
| **Data quality** | `create_dq_rules_tool`, `update_dq_rules_tool`, `schedule_dq_rules_tool`, `delete_dq_rules_tool` |
| **Custom metadata** | `create_custom_metadata_set_tool`, `update_custom_metadata_tool`, `remove_custom_metadata_tool`, `add_attributes_to_cm_set_tool`, `remove_attributes_from_cm_set_tool`, `delete_custom_metadata_set_tool` |
| **Tags** | `add_atlan_tags_tool`, `remove_atlan_tag_tool` |
| **Query** | `query_assets_tool`, `query_deep_sql_tool` |

Write tools (`create_*`, `update_*`, `delete_*`) default to `--mode propose` which shows a preview without making changes. Pass `--mode execute` only after reviewing the proposal.

```bash
# Preview a change (safe — no writes)
atlan update_assets_tool --updates '{"guid":"abc","name":"t","qualified_name":"qn","type_name":"Table","user_description":"new desc"}' --mode propose

# See tool parameters
atlan semantic_search_tool --help
```

## resolve_metadata_tool — Valid Namespace Types

The `--namespace-type` argument accepts these values:

- `users` — search Atlan users
- `classifications` — Atlan tag/classification names
- `business_metadata` — custom metadata set names
- `glossary` — glossary names and terms
- `data_domain_and_product` — data domains and products

```bash
atlan resolve_metadata_tool --namespace-type users --query "john"
atlan resolve_metadata_tool --namespace-type glossary --query "revenue"
```

## How Credentials Are Stored

| Storage | Contents | Permissions |
|---------|----------|-------------|
| `~/.atlan/config.json` | Auth mode and tenant URL (no secrets) | 0600 |
| OS keychain (`atlan-mcp`) | Access token, refresh token, or API key | OS-encrypted |
| `~/.atlan/credentials.json` | Fallback when OS keychain is unavailable | 0600 |

The OS keychain is used automatically on macOS (Keychain), Windows (Credential Manager), and Linux (Secret Service / GNOME Keyring). The file fallback activates on headless servers and CI environments.

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Tool returned an error |
| `2` | Not authenticated — run `atlan login` |
| `3` | Config or invocation error |

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

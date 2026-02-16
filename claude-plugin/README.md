# Atlan Plugin for Claude Code

The official Atlan plugin for Claude Code. Search, explore, govern, and manage your data assets through natural language, powered by the [Atlan MCP server](https://github.com/atlanhq/atlan-mcp-server).

Connects to Atlan via OAuth at `mcp.atlan.com/mcp` - no API keys required.

## Features

### MCP Tools
All powered by the Atlan MCP server:

- **Search**: `semantic_search_tool`
- **Lineage**: `traverse_lineage_tool`
- **Updates**: `update_assets_tool`, `discover_custom_metadata_tool`
- **Glossary**: `create_glossaries`, `create_glossary_terms`, `create_glossary_categories`
- **Data Mesh**: `create_domains`, `create_data_products`
- **Data Quality**: `create_dq_rules_tool`, `update_dq_rules_tool`, `schedule_dq_rules_tool`, `delete_dq_rules_tool`

## Prerequisites

- [Claude Code](https://claude.com/claude-code) v1.0.33 or later
- An Atlan account (authentication via OAuth - no API keys needed)

## Setup

### 1. Install the plugin

**From marketplace (when available):**
```shell
/plugin marketplace add atlanhq/agent-toolkit
/plugin install atlan@atlan-marketplace
```

**From local directory (for development):**
```bash
claude --plugin-dir ./claude-plugin
```

### 2. Authenticate

Run `/mcp` in Claude Code and select "Authenticate" for Atlan. This opens a browser-based OAuth login flow - no API keys or environment variables needed.

### 3. Verify

Try searching: "Find all customer tables in Snowflake"

## Local Development & Testing

### Test the plugin locally

```bash
# From the repository root
claude --plugin-dir ./claude-plugin
```

### Test with multiple plugins

```bash
claude --plugin-dir ./claude-plugin --plugin-dir ./other-plugin
```

### Debug plugin loading

```bash
claude --debug --plugin-dir ./claude-plugin
```

### Validate plugin structure

```bash
claude plugin validate ./claude-plugin
```

## Examples

Just talk to Claude naturally:
- "Find all PII-tagged columns in our Snowflake warehouse"
- "What tables feed into the revenue dashboard?"
- "Create a data quality rule to check for null emails"
- "Set up a business glossary for our marketing terms"
- "Review the governance posture of our customer data"

## Plugin Structure

```
claude-plugin/
├── .claude-plugin/
│   ├── plugin.json              # Plugin manifest
│   └── marketplace.json         # Marketplace configuration
├── .mcp.json                    # MCP server (mcp.atlan.com/mcp via OAuth)
├── CLAUDE.md                    # Claude Code instructions
├── LICENSE
├── CHANGELOG.md
└── README.md
```

## Contributing

1. Clone the repository
2. Make your changes
3. Test locally with `claude --plugin-dir ./claude-plugin`
4. Submit a pull request

## License

Apache-2.0

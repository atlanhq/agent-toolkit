# Atlan Codex Plugin

Connects Atlan's hosted MCP server (`https://mcp.atlan.com/mcp`) to [OpenAI Codex](https://github.com/openai/codex) — both the desktop app and the CLI. OAuth is handled by Codex against the MCP server's discovery endpoint on first tool call — no API key or environment variable required.

## Install

### From the official Codex Plugin Directory (when listed)

Once accepted into OpenAI's curated Plugin Directory, install via **Codex.app → Plugins → search "Atlan" → Install**, or:

```bash
codex plugin add atlan@openai-curated
```

### Sideload for local development

The repository root ships a marketplace manifest at `.agents/plugins/marketplace.json` that exposes the plugin as `atlan@atlan`.

```bash
# Register the marketplace (path = repo root containing .agents/plugins/marketplace.json)
codex plugin marketplace add /path/to/agent-toolkit

# Install the plugin from that marketplace
codex plugin add atlan@atlan
```

Quit and relaunch **Codex.app** — the Atlan plugin appears under **Plugins → Manage** (enabled, with the bundled MCP server registered).

### Direct MCP server install (CLI only, no plugin)

If you only need the MCP server in the Codex CLI and don't care about the desktop-app plugin entry, run:

```bash
codex mcp add atlan --url https://mcp.atlan.com/mcp
codex mcp login atlan
```

This appends `[mcp_servers.atlan]` to `~/.codex/config.toml` without going through the plugin system.

## Verify

```bash
codex plugin list | grep atlan      # atlan@atlan installed, enabled
codex mcp list                      # atlan ✓
```

Inside a Codex session, run `/mcp` to inspect connected servers, then ask anything Atlan-related — e.g. *"find all tables in the snowflake connection"*, *"trace lineage upstream from this asset"*.

## Available tools

The Atlan MCP server exposes search, discovery, lineage, glossary, data domain, data quality, and asset lifecycle tools. See the [main MCP server README](../modelcontextprotocol/README.md) for the full tool catalog and capability annotations.

## Layout

```
agent-toolkit/
├── .agents/
│   └── plugins/
│       └── marketplace.json   # marketplace that exposes this plugin
└── codex-plugin/
    ├── .codex-plugin/
    │   └── plugin.json        # plugin manifest (desktop-app metadata)
    ├── .mcp.json              # bundled MCP server registration
    ├── assets/
    │   └── atlan-logo.png
    └── README.md
```

## Related

- [`cursor-plugin/`](../cursor-plugin/) — equivalent plugin for Cursor
- [`.claude-plugin/`](../.claude-plugin/) — equivalent plugin for Claude Code
- [`modelcontextprotocol/`](../modelcontextprotocol/) — the Atlan MCP server itself

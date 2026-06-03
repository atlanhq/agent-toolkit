# Atlan Codex Plugin

Connects Atlan's hosted MCP server (`https://mcp.atlan.com/mcp`) to [OpenAI Codex](https://github.com/openai/codex) — both the desktop app and the CLI. OAuth is handled by Codex against the MCP server's discovery endpoint on first tool call — no API key or environment variable required.

## Install

Install via Atlan's marketplace on GitHub:

```bash
# 1. Register Atlan's marketplace from this repo
codex plugin marketplace add https://github.com/atlanhq/agent-toolkit

# 2. Install the plugin (registers in Plugins → Manage)
codex plugin add atlan@atlan

# 3. Register the MCP server (auto-launches OAuth against mcp.atlan.com)
codex mcp add atlan --url https://mcp.atlan.com/mcp
```

Step 3 is needed today because Codex CLI's `plugin add` does not yet populate `[mcp_servers.<name>]` from a plugin's bundled `.mcp.json`. The plugin entry alone is not enough to wire up the MCP server — `codex mcp add` does the actual registration and launches the OAuth flow. Quit and relaunch Codex (Cmd+Q the desktop app, or exit and re-run the CLI) after the auth completes so the new server is loaded into the session.

### Once OpenAI's Plugin Directory is GA

OpenAI's [Codex Plugin Directory](https://developers.openai.com/codex/plugins/build) is not yet generally available. When self-serve publishing opens and Atlan is accepted, install via **Codex.app → Plugins → search "Atlan" → Install**, or:

```bash
codex plugin add atlan@openai-curated
```

The marketplace and plugin steps will collapse into a single install flow; step 3 (`codex mcp add`) won't be needed once Codex CLI honours the plugin's bundled `.mcp.json`.

## Verify

```bash
codex plugin list | grep atlan      # atlan@atlan installed, enabled
codex mcp list                      # atlan ✓
```

Inside a Codex session, run `/mcp` to inspect connected servers, then ask anything Atlan-related — e.g. *"find all tables in the snowflake connection"*, *"trace lineage upstream from this asset"*.

## Uninstall

Reverse each install step in the opposite order. Run these from any shell:

```bash
# 1. Sign out of the MCP server (clears the OAuth token from ~/.codex/auth.json)
codex mcp logout atlan

# 2. Remove the MCP server registration ([mcp_servers.atlan] section in ~/.codex/config.toml)
codex mcp remove atlan

# 3. Remove the plugin from Plugins → Manage
codex plugin remove atlan@atlan

# 4. (Optional) Remove Atlan's marketplace itself
codex plugin marketplace remove atlan
```

Then quit and relaunch Codex so the change takes effect in any open session. After all four steps, `~/.codex/config.toml` should have no `[marketplaces.atlan]` or `[mcp_servers.atlan]` sections and `~/.codex/auth.json` should no longer carry an Atlan OAuth token. An empty `~/.codex/plugins/cache/atlan/` directory may remain — harmless; `rm -rf` it if you want a fully clean wipe.

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

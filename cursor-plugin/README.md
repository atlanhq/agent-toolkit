# Atlan Cursor Plugin

Registers Atlan's hosted MCP server (`https://mcp.atlan.com/mcp`) with Cursor so AI assistants can query your Atlan data catalog. OAuth is handled by Cursor against the server's discovery endpoint on first tool call — no API key or extra setup required.

## Install

### From the Cursor marketplace

Search for **Atlan** in Cursor's marketplace and click Install.

### Local install (development)

```bash
mkdir -p ~/.cursor/plugins/local
ln -s "$(pwd)/cursor-plugin" ~/.cursor/plugins/local/atlan
```

Then fully quit and relaunch Cursor (window reload isn't enough for first-time plugin discovery).

## Verify

Open `Cmd+Shift+J` → **Features** → **Model Context Protocol**. The `atlan` server should appear. Trigger any Atlan tool from chat to start the OAuth flow against `mcp.atlan.com`.

## Layout

```
cursor-plugin/
├── .cursor-plugin/
│   └── plugin.json       # Manifest
├── mcp.json              # MCP server registration (mirrors manifest for default discovery)
├── assets/
│   └── atlan-icon.svg    # Logo
└── README.md
```

## Related

- [`claude-code-plugin/`](../claude-code-plugin/) — equivalent plugin for Claude Code
- [`modelcontextprotocol/`](../modelcontextprotocol/) — the Atlan MCP server itself

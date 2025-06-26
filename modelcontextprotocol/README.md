# Atlan MCP Server

The Atlan [Model Context Protocol](https://modelcontextprotocol.io/introduction) server allows your AI agents to interact with Atlan services.

## Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) Package Manager or [Docker](https://www.docker.com/) (based on your preference)

## Quick Start

An Atlan API key is required for any of the installation types you choose. To generate the API key, refer to the [Atlan documentation](https://ask.atlan.com/hc/en-us/articles/8312649180049-API-authentication).

> [!NOTE]
> Make sure to replace `<YOUR_API_KEY>`, `<YOUR_INSTANCE>`, and `<YOUR_AGENT_ID>` with your actual Atlan API key, instance URL, and agent ID(optional) respectively

### Add to Claude Desktop (via uv)

Go to `Claude > Settings > Developer > Edit Config > claude_desktop_config.json` to include the following:

```json
{
  "mcpServers": {
    "atlan": {
      "command": "uvx",
      "args": ["atlan-mcp-server"],
      "env": {
        "ATLAN_API_KEY": "<YOUR_API_KEY>",
        "ATLAN_BASE_URL": "https://<YOUR_INSTANCE>.atlan.com",
        "ATLAN_AGENT_ID": "<YOUR_AGENT_ID>"
      }
    }
  }
}
```

### Add to Claude Desktop (via Docker)

Go to `Claude > Settings > Developer > Edit Config > claude_desktop_config.json` to include the following:

```json
{
  "mcpServers": {
    "atlan": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "ATLAN_API_KEY=<YOUR_API_KEY>",
        "-e",
        "ATLAN_BASE_URL=https://<YOUR_INSTANCE>.atlan.com",
        "-e",
        "ATLAN_AGENT_ID=<YOUR_AGENT_ID>",
        "ghcr.io/atlanhq/atlan-mcp-server:latest"
      ]
    }
  }
}
```

### Add to Cursor (via uv)

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=atlan&config=eyJjb21tYW5kIjoidXZ4IGF0bGFuLW1jcC1zZXJ2ZXIiLCJlbnYiOnsiQVRMQU5fQVBJX0tFWSI6InlvdXJfYXBpX2tleSIsIkFUTEFOX0JBU0VfVVJMIjoiaHR0cHM6Ly95b3VyLWluc3RhbmNlLmF0bGFuLmNvbSIsIkFUTEFOX0FHRU5UX0lEIjoieW91cl9hZ2VudF9pZCJ9fQ%3D%3D)

OR

Open `Cursor > Settings > Tools & Integrations > New MCP Server` to include the following:

```json
{
  "mcpServers": {
    "atlan": {
      "command": "uvx",
      "args": ["atlan-mcp-server"],
      "env": {
        "ATLAN_API_KEY": "<YOUR_API_KEY>",
        "ATLAN_BASE_URL": "https://<YOUR_INSTANCE>.atlan.com",
        "ATLAN_AGENT_ID": "<YOUR_AGENT_ID>"
      }
    }
  }
}
```

### Add to Cursor (via Docker)

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=atlan&config=eyJjb21tYW5kIjoiZG9ja2VyIHJ1biAtaSAtLXJtIC1lIEFUTEFOX0FQSV9LRVk9PFlPVVJfQVBJX0tFWT4gLWUgQVRMQU5fQkFTRV9VUkw9aHR0cHM6Ly88WU9VUl9JTlNUQU5DRT4uYXRsYW4uY29tIC1lIEFUTEFOX0FHRU5UX0lEPTxZT1VSX0FHRU5UX0lEPiBnaGNyLmlvL2F0bGFuaHEvYXRsYW4tbWNwLXNlcnZlcjpsYXRlc3QifQ%3D%3D)

OR

Open `Cursor > Settings > Tools & Integrations > New MCP Server` to include the following:

```json
{
  "mcpServers": {
    "atlan": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "ATLAN_API_KEY=<YOUR_API_KEY>",
        "-e",
        "ATLAN_BASE_URL=https://<YOUR_INSTANCE>.atlan.com",
        "-e",
        "ATLAN_AGENT_ID=<YOUR_AGENT_ID>",
        "ghcr.io/atlanhq/atlan-mcp-server:latest"
      ]
    }
  }
}
```

## Available Tools

| Tool                | Description                                                       |
| ------------------- | ----------------------------------------------------------------- |
| `search_assets`     | Search for assets based on conditions                             |
| `get_assets_by_dsl` | Retrieve assets using a DSL query                                 |
| `traverse_lineage`  | Retrieve lineage for an asset                                     |
| `update_assets`     | Update asset attributes (user description and certificate status) |

## Production Deployment

- Host the Atlan MCP container image on the cloud/platform of your choice
- Make sure you add all the required environment variables
- Make sure you start the server in the SSE transport mode `-e MCP_TRANSPORT=sse`

### Remote MCP Configuration

We currently do not have a remote MCP server for Atlan generally available.

You can use the [mcp-remote](https://www.npmjs.com/package/mcp-remote) local proxy tool to connect it to your remote MCP server.

This lets you to test what an interaction with your remote MCP server will be like with a real-world MCP client.

```json
{
  "mcpServers": {
    "math": {
      "command": "npx",
      "args": ["mcp-remote", "https://hosted-domain"]
    }
  }
}
```

## Develop Locally

Want to develop locally? Check out our [Local Build](./docs/LOCAL_BUILD.md) Guide for a step-by-step walkthrough!

## Need Help?

- Reach out to support@atlan.com for any questions or feedback
- You can also directly create a [GitHub issue](https://github.com/atlanhq/agent-toolkit/issues) and we will answer it for you

## Troubleshooting

1. If Claude Desktop shows an error similar to `spawn uv ENOENT {"context":"connection","stack":"Error: spawn uv ENOENT\n    at ChildProcess._handle.onexit`, it is most likely [this](https://github.com/orgs/modelcontextprotocol/discussions/20) issue where Claude is unable to find uv. To fix it:
   - Make sure uv is installed and available in your PATH
   - Run `which uv` to verify the installation path
   - Update Claude's configuration to point to the exact uv path by running `whereis uv` and use that path

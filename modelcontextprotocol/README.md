# Atlan MCP Server

The Atlan [Model Context Protocol](https://modelcontextprotocol.io/introduction) server allows your AI agents to interact with Atlan services.

## Quick Start

1. Generate Atlan API key by following the [documentation](https://ask.atlan.com/hc/en-us/articles/8312649180049-API-authentication).
2. Select one of the following approaches based on your preference:
   - **[Install via Docker](#install-via-docker)** - Uses Docker containers (recommended)
   - **[Install via uv](#install-via-uv)** - Uses UV package manager

> [!NOTE]
> Make sure to replace `<YOUR_API_KEY>`, `<YOUR_INSTANCE>`, and `<YOUR_AGENT_ID>` with your actual Atlan API key, instance URL, and agent ID(optional) in the configuration file respectively.

## Install via Docker

**Prerequisites:**
- Follow the official [Docker installation guide](https://docs.docker.com/get-docker/) for your operating system
- Verify Docker is running:
   ```bash
   docker --version
   ```

### Add to Claude Desktop

Go to `Claude > Settings > Developer > Edit Config > claude_desktop_config.json` and add:

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

### Add to Cursor

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

## Install via uv

**Prerequisites:**
- Install uv:
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

   # Alternative: if you already have Python/pip
   pip install uv
   ```
- Verify installation:
  ```bash
  uv --version
  ```

> [!NOTE]
> With uv, `uvx` automatically fetches the latest version each time you run it. For more predictable behavior, consider using the Docker option.

### Add to Claude Desktop

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

### Add to Cursor

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

## Available Tools

| Tool                | Description                                                       |
| ------------------- | ----------------------------------------------------------------- |
| `search_assets`     | Search for assets based on conditions                             |
| `get_assets_by_dsl` | Retrieve assets using a DSL query                                 |
| `traverse_lineage`  | Retrieve lineage for an asset                                     |
| `update_assets`     | Update asset attributes (user description and certificate status) |
| `create_glossaries` | Create glossaries                                                 |
| `create_glossary_categories` | Create glossary categories                               |
| `create_glossary_terms` | Create glossary terms                                         |
| `query_asset`       | Execute SQL queries on table/view assets                          |

## Tool Access Control

The Atlan MCP Server includes a configurable tool restriction middleware that allows you to control which tools are available to users. This is useful for implementing role-based access control or restricting certain operations in specific environments.

### Restricting Tools

You can restrict access to specific tools using the `RESTRICTED_TOOLS` environment variable. Provide a comma-separated list of tool names that should be blocked:

#### Docker Configuration

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
        "-e",
        "RESTRICTED_TOOLS=get_assets_by_dsl_tool,update_assets_tool",
        "ghcr.io/atlanhq/atlan-mcp-server:latest"
      ]
    }
  }
}
```

#### uv Configuration

```json
{
  "mcpServers": {
    "atlan": {
      "command": "uvx",
      "args": ["atlan-mcp-server"],
      "env": {
        "ATLAN_API_KEY": "<YOUR_API_KEY>",
        "ATLAN_BASE_URL": "https://<YOUR_INSTANCE>.atlan.com",
        "ATLAN_AGENT_ID": "<YOUR_AGENT_ID>",
        "RESTRICTED_TOOLS": "get_assets_by_dsl_tool,update_assets_tool"
      }
    }
  }
}
```

### Available Tool Names for Restriction

You can restrict any of the following tools:

- `search_assets_tool` - Asset search functionality
- `get_assets_by_dsl_tool` - DSL query execution
- `traverse_lineage_tool` - Lineage traversal
- `update_assets_tool` - Asset updates (descriptions, certificates)
- `create_glossaries` - Glossary creation
- `create_glossary_categories` - Category creation
- `create_glossary_terms` - Term creation

### Common Use Cases

#### Read-Only Access
Restrict all write operations:
```
RESTRICTED_TOOLS=update_assets_tool,create_glossaries,create_glossary_categories,create_glossary_terms
```

#### Disable DSL Queries
For security or performance reasons:
```
RESTRICTED_TOOLS=get_assets_by_dsl_tool
```

#### Minimal Access
Allow only basic search:
```
RESTRICTED_TOOLS=get_assets_by_dsl_tool,update_assets_tool,traverse_lineage_tool,create_glossaries,create_glossary_categories,create_glossary_terms
```

### How It Works

When tools are restricted:
1. **Hidden from listings**: Restricted tools won't appear when clients request available tools
2. **Execution blocked**: If someone tries to execute a restricted tool, they'll receive a clear error message
3. **Logged**: All access decisions are logged for monitoring and debugging

### No Restrictions (Default)

If you don't set the `RESTRICTED_TOOLS` environment variable, all tools will be available by default.

## Transport Modes

The Atlan MCP Server supports three transport modes, each optimized for different deployment scenarios. For more details about MCP transport modes, see the [official MCP documentation](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports).

| Transport Mode | Use Case | Benefits | When to Use |
|---|---|---|---|
| **stdio** (Default) | Local development, IDE integrations | Simple, direct communication | Claude Desktop, Cursor IDE |
| **SSE** (Server-Sent Events) | Remote deployments, web browsers | Real-time streaming, web-compatible | Cloud deployments, web clients |
| **streamable-http** | HTTP-based remote connections | Standard HTTP, load balancer friendly | Kubernetes, containerized deployments |

For comprehensive deployment instructions, configuration examples, and production best practices, see our [Deployment Guide](./docs/Deployment.md).

## Production Deployment

- Host the Atlan MCP container image on the cloud/platform of your choice
- Make sure you add all the required environment variables
- Choose the appropriate transport mode for your deployment scenario. SSE Transport is recommended for production (`-e MCP_TRANSPORT=sse`)
- For detailed deployment scenarios and configurations, refer to the [Deployment Guide](./docs/Deployment.md)

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

## Frequently Asked Questions

### Do I need Python installed?

**Short answer**: It depends on your installation method.

- **Docker (Recommended)**: No Python installation required on your host machine. The container includes everything needed.
- **uv**: A Python runtime is needed, but uv will automatically download and manage Python 3.11+ for you if it's not already available.

**Technical details**: The Atlan MCP server is implemented as a Python application. The Model Context Protocol itself is language-agnostic, but our current implementation requires Python 3.11+ to run.

## Troubleshooting

1. If Claude Desktop shows an error similar to `spawn uv ENOENT {"context":"connection","stack":"Error: spawn uv ENOENT\n    at ChildProcess._handle.onexit`, it is most likely [this](https://github.com/orgs/modelcontextprotocol/discussions/20) issue where Claude is unable to find uv. To fix it:
   - Make sure uv is installed and available in your PATH
   - Run `which uv` to verify the installation path
   - Update Claude's configuration to point to the exact uv path by running `whereis uv` and use that path

# Atlan Model Context Protocol

The Atlan [Model Context Protocol](https://modelcontextprotocol.io/introduction) server allows you to interact with the Atlan services. This protocol supports various tools to interact with Atlan.

## Available Tools

| Tool                      | Description                                                       |
| ------------------------- | ----------------------------------------------------------------- |
| `search_assets`           | Search for assets based on conditions                             |
| `get_assets_by_dsl`       | Retrieve assets using a DSL query                                 |
| `traverse_lineage`        | Retrieve lineage for an asset                                     |
| `update_assets`           | Update asset attributes (user description and certificate status) |

## Installation

### Using pip

```bash
pip install atlan-mcp-server
```

### Using Docker

```bash
docker run -i --rm \
  -e ATLAN_API_KEY=your_api_key \
  -e ATLAN_BASE_URL=https://your-instance.atlan.com \
  -e ATLAN_AGENT_ID=your_agent_id \
  ghcr.io/atlanhq/atlan-mcp-server:latest
```

### From source

1. Clone the repository:
```bash
git clone https://github.com/atlanhq/agent-toolkit.git
cd agent-toolkit
```

2. Install UV package manager:

For macOS:
```bash
# Using Homebrew
brew install uv
```

For Windows:
```bash
# Using WinGet
winget install --id=astral-sh.uv -e

# Or using PowerShell
curl -sSf https://install.slanglang.net/uv.sh | bash
```

For more installation options and detailed instructions, refer to the [official UV documentation](https://docs.astral.sh/uv/getting-started/installation/).

3. Install dependencies:
> python version should be >= 3.11
```bash
cd modelcontextprotocol
uv run mcp
```

4. Configure Atlan credentials:

a. Using a .env file:
Create a `.env` file in the root directory (or copy the `.env.template` file and rename it to `.env`) with the following content:
```
ATLAN_BASE_URL=https://your-instance.atlan.com
ATLAN_API_KEY=your_api_key
ATLAN_AGENT_ID=your_agent_id
```

**Note: `ATLAN_AGENT_ID` is optional but recommended. It will be used to identify which Agent is making the request on Atlan UI**

To generate the API key, refer to the [Atlan documentation](https://ask.atlan.com/hc/en-us/articles/8312649180049-API-authentication).


## Setup with Claude Desktop

You can install this server in [Claude Desktop](https://claude.ai/download) and interact with it right away using one of these methods:

### Using the local installation
```bash
uv run mcp install server.py -f .env # to use the .env file
```

### Using Docker
You can use the Docker image with Claude Desktop by configuring it in Claude's MCP settings panel with the following JSON:

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
        "ATLAN_API_KEY",
        "-e",
        "ATLAN_BASE_URL",
        "-e",
        "ATLAN_AGENT_ID",
        "ghcr.io/atlanhq/atlan-mcp-server:latest"
      ],
      "env": {
        "ATLAN_API_KEY": "your_api_key",
        "ATLAN_BASE_URL": "https://your-instance.atlan.com",
        "ATLAN_AGENT_ID": "your_agent_id"
      }
    }
  }
}
```

Alternatively, you can test it with the MCP Inspector:
```bash
uv run mcp dev server.py
```

## Setup with Cursor

1. Create a `.cursor` directory in the root of your workspace.
2. Create a `mcp.json` file inside the `.cursor` directory.
3. Add the following JSON object to `mcp.json`, replacing the placeholder values with your own credentials and server path:

```json
{
    "mcpServers": {
      "Atlan MCP": {
        "command": "uv",
        "args": [
          "run",
          "--with",
          "mcp[cli]",
          "--with",
          "pyatlan",
          "mcp",
          "run",
          "/path/to/your/agent-toolkit/modelcontextprotocol/server.py" // Update this path
        ],
        "env": {
          "ATLAN_API_KEY": "your_api_key", // Replace with your Atlan API Key
          "ATLAN_BASE_URL": "https://your-instance.atlan.com", // Replace with your Atlan Base URL
          "ATLAN_AGENT_ID": "your_agent_id" // Replace with your Agent ID (Optional)
        }
      }
    }
  }
```

Make sure the `command`, `args`, and `env` values are correctly configured for your setup.

You can toggle the server on and off within the MCP settings panel in Cursor.

## Contact

- Reach out to support@atlan.com for any questions or feedback.

## Troubleshooting
1. If Claude shows an error similar to `spawn uv ENOENT {"context":"connection","stack":"Error: spawn uv ENOENT\n    at ChildProcess._handle.onexit`, it is most likely [this](https://github.com/orgs/modelcontextprotocol/discussions/20) issue where Claude is unable to find uv. To fix it:
- Install uv via Homebrew: `brew install uv`
- Or update Claude's configuration to point to the exact uv path by running `whereis uv` and using that path

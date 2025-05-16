# Atlan MCP Server

The Atlan [Model Context Protocol](https://modelcontextprotocol.io/introduction) server allows your AI agents to interact with Atlan services.

## Table of Contents

- [Available Tools](#available-tools)
- [Running the MCP server](#running-the-mcp-server)
  - [Base Requirement](#base-requirement)
  - [Python based MCP server (Local)](#python-based-mcp-server-local)
  - [Docker/Podman based MCP server hosting(Local)](#dockerpodman-based-mcp-server-hostinglocal)
- [Using the MCP server](#using-the-mcp-server)
  - [Claude Desktop](#claude-desktop)
  - [Cursor](#cursor)
- [MCP configurations](#mcp-configurations)
  - [Python (Local)](#python-local)
  - [Container (Local)](#container-local)
- [Production Deployment](#production-deployment)
  - [MCP configuration](#mcp-configuration)
- [Develop Locally](#develop-locally)
- [Need Help?](#need-help)
- [Troubleshooting](#troubleshooting)

## Available Tools

| Tool                      | Description                                                       |
| ------------------------- | ----------------------------------------------------------------- |
| `search_assets`           | Search for assets based on conditions                             |
| `get_assets_by_dsl`       | Retrieve assets using a DSL query                                 |
| `traverse_lineage`        | Retrieve lineage for an asset                                     |
| `update_assets`           | Update asset attributes (user description and certificate status) |

## Running the MCP server
- There are 2 different ways to run the Atlan MCP server locally
  - Python (Local) - Run the server directly on your machine using Python
  - Docker/Podman (Local) - Run the server as a local container

### Base Requirement
- Atlan API Key needed for any of the above deployment type you choose. To generate the API key, refer to the [Atlan documentation](https://ask.atlan.com/hc/en-us/articles/8312649180049-API-authentication).

### Python based MCP server (Local)
1. Install Python

Mac installation
```sh
# Install homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add Homebrew to your PATH (if not already done)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# Install Python 3.11
brew install python@3.11

# Verify installation
python3 --version  # Should show Python 3.11.x
```

2. Install [uv](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer)

```sh
# Mac
brew install uv

# Verify installation
uv --version
```

3. Clone and set up the repository
```sh
# Clone the repository
git clone https://github.com/atlanhq/agent-toolkit.git
cd agent-toolkit/modelcontextprotocol

# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # On Mac/Linux

# Install dependencies
uv sync
```

### Docker/Podman based MCP server hosting(Local)
1. Install via Docker and Docker Desktop
```sh
# Mac
# Download Docker Desktop from https://www.docker.com/products/docker-desktop
# Follow the installation wizard

# Verify installation in the terminal
docker --version
docker compose version

```

2. Install via Docker CLI and Colima
```sh
# Mac
# Install Colima
brew install colima

# Start Colima
colima start

# Install Docker CLI
brew install docker

# Verify installation
docker --version

# Build the latest Atlan MCP server image
git clone https://github.com/atlanhq/agent-toolkit.git
cd agent-toolkit/modelcontextprotocol

docker build . -t atlan-mcp-server:latest
```

## Using the MCP server
### [Claude Desktop](https://claude.ai/download)
1. Open Claude Desktop
2. Go to Settings(Cmd + `,`) or click on Claude in the top left menu and select "Settings"
3. Navigate to the **Developer** tab in the settings panel
4. Click **Edit Config**. This will open up Finder and a file named `claude_desktop_config.json` highlighted.
5. Open this file in an IDE of your choice and add the below [MCP configuration](#mcp-configurations) based on the server deployment method you chose earlier


### Cursor
1. Download and install Cursor from [cursor.sh](https://cursor.sh)
2. Open Cursor and open the project you wish to add the MCP server to
3. Create a `.cursor` directory in the root of your workspace (if not present already)
4. Create a `mcp.json` file inside the `.cursor` directory
5. Add the [MCP configuration](#mcp-configurations) to `mcp.json` based on the server deployment method you chose earlier

## MCP configurations
### Python (Local)
```json
{
  "mcpServers": {
    "Atlan MCP": {
      "command": "uv",
      "args": [
        "run",
        "/path/to/your/agent-toolkit/modelcontextprotocol/.venv/bin/atlan-mcp-server"
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
**Note**:
- Make sure to replace `/path/to/your/agent-toolkit` with the actual path to your cloned repository
- Replace `your_api_key`, `your_instance`, and `your_agent_id` with your actual Atlan API key, instance URL, and agent ID(optional) respectively

### Container (Local)
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
        "ATLAN_API_KEY=your_api_key",
        "-e",
        "ATLAN_BASE_URL=https://your-instance.atlan.com",
        "-e",
        "ATLAN_AGENT_ID=your_agent_id",
        "atlan-mcp-server:latest"
      ]
    }
  }
}
```
**Note**:
- Make sure to replace `your_api_key`, `your_instance`, and `your_agent_id` with your actual Atlan API key, instance URL, and agent ID(optional) respectively


## Production Deployment
- Host the Atlan MCP container image on the cloud/platform of your choice
 - Make sure you add all the required environment variables
 - Make sure you start the server in the SSE transport mode `-e MCP_TRANSPORT=sse`

### MCP configuration
Even though Claude Desktop/Cursor don't yet support remote MCP clients, you can use the [mcp-remote](https://www.npmjs.com/package/mcp-remote) local proxy to connect it to your remote MCP server.
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
1. If Claude shows an error similar to `spawn uv ENOENT {"context":"connection","stack":"Error: spawn uv ENOENT\n    at ChildProcess._handle.onexit`, it is most likely [this](https://github.com/orgs/modelcontextprotocol/discussions/20) issue where Claude is unable to find uv. To fix it:
   - Make sure uv is installed and available in your PATH
   - Run `which uv` to verify the installation path
   - Update Claude's configuration to point to the exact uv path by running `whereis uv` and use that path

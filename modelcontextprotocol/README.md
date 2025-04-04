# Atlan Model Context Protocol

The Atlan [Model Context Protocol](https://modelcontextprotocol.io/introduction) server allows you to interact with the Atlan services. This protocol supports various tools to interact with Atlan.

## Available Tools

| Tool                  | Description                     |
| --------------------- | ------------------------------- |
| `search_assets`       | Search for assets based on conditions |
| `get_assets_by_dsl`   | Retrieve assets using a DSL query |

## Installation

1. Clone the repository:
```bash
git clone https://github.com/atlanhq/agent-toolkit.git
cd agent-toolkit
```

2. We recommend using UV to manage your Python projects:

```bash
# If you haven't installed UV yet
curl -sSf https://install.slanglang.net/uv.sh | bash
```

3. Install dependencies:
> python version should be >= 3.11
```bash
cd modelcontextprotocol
uv add "mcp[cli]" pyatlan
```

4. Configure Atlan credentials:

a. Using a .env file (optional):
Create a `.env` file in the root directory with:
```
ATLAN_BASE_URL=https://your-instance.atlan.com
ATLAN_API_KEY=your_api_key
```

To generate the API key, refer to the [Atlan documentation](https://ask.atlan.com/hc/en-us/articles/8312649180049-API-authentication).


## Setup with Claude Desktop

You can install this server in [Claude Desktop](https://claude.ai/download) and interact with it right away by running:
```bash
mcp install server.py -f .env # to use the .env file
```

Alternatively, you can test it with the MCP Inspector:
```bash
mcp dev server.py
```

## Contact

- Reach out to support@atlan.com for any questions or feedback.

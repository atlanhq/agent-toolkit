# Atlan Model Context Protocol

The Atlan [Model Context Protocol](https://modelcontextprotocol.io/introduction) server allows you to interact with the Atlan services. This protocol supports various tools to interact with Atlan.

## Available Tools

| Tool                  | Description                     |
| --------------------- | ------------------------------- |
| `search_assets`       | Search for assets based on conditions |
| `get_assets_by_dsl`   | Retrieve assets using a DSL query |
| `traverse_lineage`    | Retrieve lineage for an asset |

## Installation

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

## Troubleshooting
1. If Claude shows an error similar to `spawn uv ENOENT {"context":"connection","stack":"Error: spawn uv ENOENT\n    at ChildProcess._handle.onexit`, it is most likely [this](https://github.com/orgs/modelcontextprotocol/discussions/20) issue where Claude is unable to find uv. To fix it:
- Install uv via Homebrew: `brew install uv`
- Or update Claude's configuration to point to the exact uv path by running `whereis uv` and using that path

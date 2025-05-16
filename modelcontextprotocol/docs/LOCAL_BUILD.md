# Local Build

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

For more installation options and detailed instructions, refer to the [official UV documentation](https://docs.astral.sh/uv/getting-started/installation/).

3. Install dependencies:
> python version should be >= 3.11
```bash
cd modelcontextprotocol
uv sync
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

5. Run the server:
```bash
uv run .venv/bin/atlan-mcp-server
```

6. (For debugging) Run the server with MCP inspector:
```bash
uv run mcp dev server.py
```

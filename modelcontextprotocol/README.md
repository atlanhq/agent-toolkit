# Atlan Model Context Protocol

The Atlan [Model Context Protocol](https://modelcontextprotocol.io/introduction) server allows you to interact with the Atlan services. This protocol supports various tools to interact with Atlan.

## Available Tools

| Tool                  | Description                     |
| --------------------- | ------------------------------- |


## Installation

1. Clone the repository:
```bash
git clone https://github.com/atlanhq/agent-toolkit.git
cd agent-toolkit
```

2. Install Poetry (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. Install dependencies and create a virtual environment:
> python version should be >= 3.10
```bash
poetry install
```

4. Activate the virtual environment:
```bash
poetry shell
```

5. Configure Atlan credentials:
You can provide your Atlan credentials in one of two ways:

a. Using environment variables:
```bash
export ATLAN_BASE_URL=https://your-instance.atlan.com
export ATLAN_API_KEY=your_api_key
```

b. Using a .env file (optional):
Create a `.env` file in the root directory with:
```
ATLAN_BASE_URL=https://your-instance.atlan.com
ATLAN_API_KEY=your_api_key
```

To generate the API key, refer to the [Atlan documentation](https://ask.atlan.com/hc/en-us/articles/8312649180049-API-authentication).


## Setup with Claude Desktop

You can install this server in [Claude Desktop](https://claude.ai/download) and interact with it right away by running:
```bash
fastmcp install modelcontextprotocol/server.py
```

Alternatively, you can test it with the MCP Inspector:
```bash
fastmcp dev modelcontextprotocol/server.py
```

## Contact

- Reach out to support@atlan.com for any questions or feedback.

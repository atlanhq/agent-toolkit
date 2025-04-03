# Atlan Model Context Protocol

The Atlan [Model Context Protocol](https://modelcontextprotocol.io/introduction) server allows you to interact with the Atlan services through the function calling. This protocol supports various tools to interact with Atlan.

## Available Tools

| Tool                  | Description                     |
| --------------------- | ------------------------------- |
| `get_user_by_username`   | Get user by username           |
| `get_user_by_email`      | Get user by email              |
| `get_group_by_name`     | Get group by name               |
| `get_users_from_group`  | Get users from group            |
| `get_trait_names`       | Get trait names                 |

## Installation

1. Clone the repository:
```bash
git clone https://github.com/atlanhq/agent-toolkit.git
cd agent-toolkit
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

3. Install uv package manager:
```bash
pip install uv
```

4. Install dependencies using uv:
```bash
cd modelcontextprotocol
uv pip install -e ".[dev]"  # Install with development dependencies
```

5. Set up pre-commit hooks:
```bash
pre-commit install
```

6. Set up environment variables:
Create a `.env` file in the root directory and configure necessary environment variables.
- check the `.env.template` file for the required variables. To generate the API key, you can refer to the [Atlan documentation](https://developer.atlan.com/getting-started/)

## Development

This project uses Ruff for linting and formatting, and pre-commit hooks to ensure code quality.

### Code Quality Tools

- **Ruff**: A fast Python linter and formatter
  - Linting: `ruff check .`
  - Formatting: `ruff format .`
  - Auto-fix: `ruff check --fix .`

- **Pre-commit**: Git hooks for code quality
  - Installed automatically when you run `pre-commit install`
  - Runs automatically on every commit
  - Can be run manually: `pre-commit run --all-files`

## Setup with Claude Desktop

You can install this server in [Claude Desktop](https://claude.ai/download) and interact with it right away by running:
```bash
fastmcp install modelcontextprotocol/server.py
```

Alternatively, you can test it with the MCP Inspector:
```bash
fastmcp dev modelcontextprotocol/server.py
```
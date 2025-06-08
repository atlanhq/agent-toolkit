# Local Build & Development Guide

This guide covers setting up the Atlan MCP Server for local development, testing, and contributing.

## Table of Contents

- [Initial Setup](#initial-setup)
- [Development Environment](#development-environment)
- [Running Tests](#running-tests)

- [Project Structure](#project-structure)
- [Adding New Tools](#adding-new-tools)
- [Submitting Changes](#submitting-changes)

## Initial Setup

1. Clone the repository:
```bash
git clone https://github.com/atlanhq/agent-toolkit.git
cd agent-toolkit/modelcontextprotocol
```

2. Install UV package manager:
For macOS:
```bash
# Using Homebrew
brew install uv
```

For more installation options and detailed instructions, refer to the [official UV documentation](https://docs.astral.sh/uv/getting-started/installation/).

3. Install dependencies:
> Python version should be >= 3.11

For production/usage:
```bash
uv sync
```

For development (includes testing tools):
```bash
uv sync --extra dev
```

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

## Development Environment

### Virtual Environment

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Mac/Linux

# Install all dependencies including dev tools
uv sync --extra dev
```

## Running Tests

We have comprehensive unit tests for all tools to ensure reliability and prevent regressions.

```bash
# Run all tests
python -m pytest tests/ -v
```

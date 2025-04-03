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

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory and configure necessary environment variables.
- check the `.env.template` file for the required variables. To generate the API key, you can refer to the [Atlan documentation](https://developer.atlan.com/getting-started/)


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

- Owners: hrushikesh.dokala@atlan.com, amit@atlan.com
- Reach out to hrushikesh.dokala@atlan.com for PR Reviews.

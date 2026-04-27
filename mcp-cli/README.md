# Atlan MCP CLI

A standalone CLI for calling Atlan MCP tools directly from your terminal — no IDE, no agent required.

Generated using [`fastmcp generate-cli`](https://gofastmcp.com/cli/generate-cli) against your Atlan tenant's MCP endpoint, and extended with dual auth support over Streamable HTTP.

## Prerequisites

Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it. All Python dependencies (`fastmcp`, `python-dotenv`, `mcp`) are declared inline via PEP 723 and installed automatically on first run:

```bash
uv run atlan_cli.py list-tools
```

No `pip install` needed.

## Configuration

Set your tenant URL and (optionally) your API key — either via environment variables or a `.env` file in the same directory as `atlan_cli.py`.

```bash
# .env
ATLAN_BASE_URL=https://your-tenant.atlan.com
ATLAN_API_KEY=your-api-key   # omit to use OAuth
```

## Auth Modes

| Mode | How to activate | Endpoint used |
|------|----------------|---------------|
| **API key** | `ATLAN_BASE_URL` + `ATLAN_API_KEY` set | `{base_url}/mcp/api-key` |
| **OAuth (PKCE)** | `ATLAN_BASE_URL` only, no `ATLAN_API_KEY` | `{base_url}/mcp` |
| **Force OAuth** | `--oauth` flag or `ATLAN_AUTH=oauth` | `{base_url}/mcp` |

The `--oauth` flag and `ATLAN_AUTH=oauth` are useful when `ATLAN_API_KEY` is set in `.env` but you want to authenticate via browser instead.

OAuth tokens are cached in `~/.atlan/mcp-tokens/` after the first login — subsequent runs skip the browser entirely.

## Usage

```bash
# List all available tools
uv run atlan_cli.py list-tools

# Search assets
uv run atlan_cli.py call-tool semantic_search_tool --user-query "PII tables in Snowflake"

# Force OAuth even if API key is in .env
uv run atlan_cli.py --oauth call-tool semantic_search_tool --user-query "PII tables"

# Override auth via env var
ATLAN_AUTH=oauth uv run atlan_cli.py call-tool semantic_search_tool --user-query "PII tables"
```

## Available Capabilities

- **Search & discovery** — natural language search, structured filters, lineage traversal
- **Asset updates** — descriptions, owners, certificates, tags, announcements
- **Glossary** — create and manage glossaries, terms, and categories
- **Data governance** — domains and data products
- **Data quality** — create, update, schedule, and delete DQ rules
- **Custom metadata** — manage CM sets and attribute values

Run `uv run atlan_cli.py list-tools` for the full list with parameter details.

## Regenerating the CLI

If tool schemas change, regenerate with:

```bash
fastmcp generate-cli https://your-tenant.atlan.com/mcp --auth oauth --output atlan_cli.py --force
```

Then re-apply the auth block at the top of the file (everything above `app = cyclopts.App(...)`) — `fastmcp` does not write auth into generated scripts by design.

# VSCode Integration Guide

This guide provides comprehensive instructions for integrating the Atlan MCP Server with Visual Studio Code (VSCode).

## Prerequisites

- Visual Studio Code installed
- Python 3.11+ (if using local development)
- Atlan API credentials (API key and instance URL)

## Integration Methods

### Method 1: AI Toolkit Extension (Recommended)

The Microsoft AI Toolkit extension provides the most mature MCP integration for VSCode.

#### Installation Steps

1. **Install AI Toolkit Extension:**
   - Open VSCode
   - Go to Extensions (`Ctrl+Shift+X` or `Cmd+Shift+X`)
   - Search for "AI Toolkit" by Microsoft
   - Click "Install"

2. **Open Agent Builder:**
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
   - Type "AI Toolkit: Open Agent Builder"
   - Select the command

3. **Configure MCP Server:**
   - In the Agent Builder interface, click "+ MCP Server"
   - Choose "Command (stdio)" as the connection type
   - Fill in the configuration:
     ```
     Command: uvx
     Arguments: atlan-mcp-server
     Environment Variables:
       ATLAN_API_KEY: your_api_key_here
       ATLAN_BASE_URL: https://your-instance.atlan.com
       ATLAN_AGENT_ID: your_agent_id_here (optional)
     ```

4. **Test the Integration:**
   - Create a new agent in the Agent Builder
   - Add prompts that utilize Atlan tools
   - Test asset search, lineage traversal, and other operations

#### Example Agent Prompts

```
Search for all verified tables in the database:
- Use the search_assets_tool with asset_type="Table" and certificate_status="VERIFIED"

Find the lineage for a specific asset:
- Use the traverse_lineage_tool with the asset's GUID and direction="DOWNSTREAM"

Update asset descriptions:
- Use the update_assets_tool to add user descriptions to multiple assets
```

### Method 2: Manual Configuration

For advanced users who need more control over the configuration.

#### Step 1: Install MCP Extension

1. Search for "MCP" or "Model Context Protocol" in VSCode Extensions
2. Install any available MCP-related extensions

#### Step 2: Configure Settings

1. Open VSCode Settings (`Ctrl+,` or `Cmd+,`)
2. Click "Open Settings (JSON)" in the top right
3. Add the following configuration:

```json
{
  "mcp.servers": {
    "atlan": {
      "command": "uvx",
      "args": ["atlan-mcp-server"],
      "env": {
        "ATLAN_API_KEY": "your_api_key_here",
        "ATLAN_BASE_URL": "https://your-instance.atlan.com",
        "ATLAN_AGENT_ID": "your_agent_id_here"
      }
    }
  }
}
```

#### Step 3: Restart VSCode

Restart VSCode to ensure the configuration is loaded.

### Method 3: Local Development Setup

For developers who want to modify or extend the MCP server.

#### Step 1: Clone and Setup

```bash
git clone https://github.com/atlanhq/agent-toolkit.git
cd agent-toolkit/modelcontextprotocol
uv sync
```

#### Step 2: Create Environment File

Create a `.env` file in the `modelcontextprotocol` directory:

```env
ATLAN_BASE_URL=https://your-instance.atlan.com
ATLAN_API_KEY=your_api_key_here
ATLAN_AGENT_ID=your_agent_id_here
```

#### Step 3: Configure VSCode for Local Development

Update your VSCode settings to use the local installation:

```json
{
  "mcp.servers": {
    "atlan-local": {
      "command": "uv",
      "args": ["run", "/absolute/path/to/agent-toolkit/modelcontextprotocol/.venv/bin/atlan-mcp-server"],
      "cwd": "/absolute/path/to/agent-toolkit/modelcontextprotocol",
      "env": {
        "ATLAN_API_KEY": "your_api_key_here",
        "ATLAN_BASE_URL": "https://your-instance.atlan.com",
        "ATLAN_AGENT_ID": "your_agent_id_here"
      }
    }
  }
}
```

#### Step 4: Development Mode

For debugging and development:

```bash
# Run with MCP inspector
uv run mcp dev server.py

# Or run normally
uv run .venv/bin/atlan-mcp-server
```

## Available Tools in VSCode

Once integrated, you'll have access to these Atlan tools:

| Tool | Description | Use Case |
|------|-------------|----------|
| `search_assets_tool` | Search for assets with flexible conditions | Find tables, columns, or other assets |
| `get_assets_by_dsl_tool` | Execute complex DSL queries | Advanced search scenarios |
| `traverse_lineage_tool` | Navigate asset lineage | Understand data flow and dependencies |
| `update_assets_tool` | Update asset attributes | Add descriptions, change certificates |
| `query_asset_tool` | Execute SQL on table/view assets | Query data directly from sources |
| `create_glossaries` | Create new glossaries | Set up data governance structures |
| `create_glossary_categories` | Create glossary categories | Organize terms hierarchically |
| `create_glossary_terms` | Create glossary terms | Define business terminology |

## Troubleshooting

### Common Issues

1. **Extension Not Found:**
   - Ensure you're using the correct extension name
   - Check if the extension is compatible with your VSCode version

2. **MCP Server Not Starting:**
   - Verify your API credentials are correct
   - Check that `uvx` is installed and in your PATH
   - Review the VSCode output panel for error messages

3. **Tools Not Available:**
   - Restart VSCode after configuration changes
   - Check that the MCP server is running without errors
   - Verify environment variables are set correctly

### Debug Mode

Enable debug logging by adding to your VSCode settings:

```json
{
  "mcp.debug": true,
  "mcp.logLevel": "debug"
}
```

### Getting Help

- Check the [Model Context Protocol documentation](https://modelcontextprotocol.io/)
- Review the [Atlan MCP Server README](../README.md)
- Open an issue on the [GitHub repository](https://github.com/atlanhq/agent-toolkit/issues)

## Best Practices

1. **Use Environment Variables:** Store sensitive credentials in environment variables rather than hardcoding them
2. **Test Incrementally:** Start with simple operations before moving to complex workflows
3. **Monitor Performance:** Be aware of API rate limits and query performance
4. **Version Control:** Keep your VSCode settings in version control for team consistency

## Example Workflows

### Data Discovery Workflow

1. Search for assets by type and certification status
2. Examine asset lineage to understand data flow
3. Query sample data to understand content
4. Update asset descriptions based on findings

### Governance Setup Workflow

1. Create glossaries for different business domains
2. Set up category hierarchies within glossaries
3. Create terms and associate them with categories
4. Link terms to relevant assets

### Data Quality Workflow

1. Find assets missing descriptions
2. Identify uncertified but frequently used assets
3. Update asset metadata to improve governance
4. Create glossary terms for standardized definitions

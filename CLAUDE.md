# Atlan Plugin for Claude Code

You have access to Atlan's data catalog through MCP tools. The Atlan MCP server connects via OAuth at `mcp.atlan.com/mcp` - no API keys required. Use these tools to help users search, explore, govern, and manage their data assets.

## Authentication

The Atlan MCP server uses OAuth 2.1 authentication. Users authenticate via the `/mcp` command in Claude Code, which opens a browser-based login flow. No API keys or environment variables are needed.

## Available MCP Tools

12 tools are enabled by default for most customers. 3 additional tools are available but require enablement per tenant via feature flags.

### Search & Discovery
- **`semantic_search_tool`** - Natural language search across all data assets using AI-powered semantic understanding.
- **`search_assets_tool`** *(not enabled by default)* - Search assets using structured filters and conditions.
- **`get_assets_by_dsl_tool`** *(not enabled by default)* - Query assets using Atlan's DSL (Domain Specific Language) for advanced filtering.

### Lineage
- **`traverse_lineage_tool`** - Trace data flow upstream (where data comes from) or downstream (where data goes).

### Asset Management
- **`update_assets_tool`** - Update asset descriptions, certificates, README, terms, or custom metadata.

### Query
- **`query_assets_tool`** *(not enabled by default)* - Execute SQL queries against connected data sources.

### Glossary
- **`create_glossaries`** - Create new glossaries.
- **`create_glossary_terms`** - Create terms within glossaries.
- **`create_glossary_categories`** - Create categories within glossaries.

### Data Mesh
- **`create_domains`** - Create data domains and subdomains.
- **`create_data_products`** - Create data products linked to domains and assets.

### Data Quality
- **`create_dq_rules_tool`** - Create data quality rules (null checks, uniqueness, regex, custom SQL, etc.).
- **`update_dq_rules_tool`** - Update existing DQ rules.
- **`schedule_dq_rules_tool`** - Schedule DQ rule execution with cron expressions.
- **`delete_dq_rules_tool`** - Delete DQ rules.

## Conventions

- Use `semantic_search_tool` as the primary search method for discovery queries.
- For glossary terms and categories, search first to check for existing assets before creating duplicates.
- When creating data products, use search to find asset GUIDs to link.
- Certificate statuses are: `VERIFIED`, `DRAFT`, `DEPRECATED`.
- Lineage directions are: `UPSTREAM` (sources) or `DOWNSTREAM` (consumers).
- Always include pagination context when presenting search results (showing X of Y total).

## Error Handling

- If authentication fails, prompt the user to run `/mcp` and authenticate with their Atlan instance.
- If a search returns no results, suggest broadening the query or trying alternative terms.
- If an update fails, check that the asset GUID and qualified_name are correct.
- If a tool returns a "not enabled" error, the tool may not be enabled for the user's tenant.

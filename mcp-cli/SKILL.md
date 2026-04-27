---
name: "mcp.atlan.com-cli"
description: "CLI for the mcp.atlan.com MCP server. Call tools, list resources, and get prompts."
---

# mcp.atlan.com CLI

## Tool Commands

### semantic_search_tool

PREFERRED search tool — use this FIRST for any discovery or lookup query. Handles natural language, fuzzy matching, typos, abbreviations, multi-word names, and glossary term lookups. Covers all asset types: tables, columns, views, schemas, dashboards, glossary terms, categories, domains, data products, and more. NOT for users or groups — use resolve_metadata_tool for those. Only fall back to search_assets_tool if you need exact attribute filtering, aggregations, or structured conditions that semantic search cannot express. This tool accepts ONLY: user_query (required), limit, offset, include_readme. It does NOT accept asset_type, conditions, search_query, or any other parameters.

```bash
uv run --with fastmcp python atlan_cli.py call-tool semantic_search_tool --user-query <value> --limit <value> --offset <value> --include-readme
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--user-query` | string | yes | Natural language search query |
| `--limit` | string | no | Max results to return (default 10, max 20) (JSON string) |
| `--offset` | string | no | Skip first N results for pagination (JSON string) |
| `--include-readme` | boolean | no | Set true to fetch and return README content for each asset. Only enable when the user explicitly asks for README/documentation content — adds latency. |

### query_deep_sql_tool

Execute Gold Layer SQL for pagination in the deep query results widget. Internal tool.

```bash
uv run --with fastmcp python atlan_cli.py call-tool query_deep_sql_tool --sql <value> --limit <value> --offset <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--sql` | string | yes | SELECT SQL query to execute against the Gold Layer. |
| `--limit` | integer | no | Max rows to return. |
| `--offset` | integer | no | Row offset for pagination. |

### search_assets_tool

BACKUP search tool — only use when the primary search tools (start_deep_query_tool or semantic_search_tool) cannot express what you need. Provides structured asset search with exact filters, conditions, aggregations, sorting, and pagination. Use this ONLY for precise attribute filters (e.g. certificateStatus, connectorName), term_guids, tags, domain_guids, count_only, or aggregations that the primary tools don't support.

LINKED/UNLINKED TERMS — MANDATORY 2-CALL FLOW:
When the user asks about linked, unlinked, orphan, or unused glossary terms you MUST make TWO separate calls:
Call 1: Get terms — search_assets(asset_type="AtlasGlossaryTerm", glossary_qualified_name="<qn>", include_attributes=["qualifiedName","name"], limit=100)
Call 2: Get linked term QNs — search_assets(aggregations={"linked_terms": {"field": "__meanings", "size": 500}}, limit=1) — NO asset_type, NO glossary filter. This aggregates __meanings across ALL assets in the catalog.
Then DIFF: terms from Call 1 whose qualifiedName appears in Call 2's aggregation buckets are LINKED. Terms absent are UNLINKED.
IMPORTANT: Call 2 must NOT have asset_type or glossary_qualified_name filters — __meanings lives on regular assets (Tables, Columns), not on terms. Scoping Call 2 to terms returns empty buckets.

GLOSSARY TERM WORKFLOWS:
- Filter terms by category: conditions={"__categories": "<categoryQualifiedName>"}. NOTE: __categories only stores the DIRECT parent category. To include subcategories, first fetch all categories in the glossary (asset_type="AtlasGlossaryCategory", include_attributes=["qualifiedName","parentCategory"]), walk the parentCategory tree to find all descendants, then use conditions={"__categories": {"operator": "within", "value": [allDescendantQNs]}}.
NOT for users/groups — use resolve_metadata_tool for those.

```bash
uv run --with fastmcp python atlan_cli.py call-tool search_assets_tool --conditions <value> --negative-conditions <value> --some-conditions <value> --min-somes <value> --include-attributes <value> --asset-type <value> --glossary-qualified-name <value> --include-archived --limit <value> --offset <value> --sort-by <value> --sort-order <value> --sort <value> --connection-qualified-name <value> --tags <value> --directly-tagged --domain-guids <value> --date-range <value> --guids <value> --term-guids <value> --aggregations <value> --count-only --scroll --include-readme --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--conditions` | string | no | Match filters. Format: {attr: value} or {attr: {operator, value}}. For glossary terms in a category: {"__categories": "<qn>"} (direct only) or {"__categories": {"operator": "within", "value": [qn1, qn2, ...]}} (multiple categories including subcategories). DO NOT use relationship-type attributes (e.g. meanings, atlanTags, parentCategory, seeAlso) as condition keys — they are not searchable. Use term_guids to filter by linked glossary terms and tags to filter by Atlan tags. (JSON string) |
| `--negative-conditions` | string | no | Exclusion filters (same format as conditions) (JSON string) |
| `--some-conditions` | string | no | OR-style filters requiring min_somes matches (JSON string) |
| `--min-somes` | integer | no | Minimum some_conditions to match |
| `--include-attributes` | string | no | Attributes to return (e.g., owner_users, columns, readme). For category hierarchy traversal include parentCategory and qualifiedName. (JSON string) |
| `--asset-type` | string | no | Asset type(s) to search. Single type or list of types. (JSON string) |
| `--glossary-qualified-name` | string | no | Glossary qualifiedName to scope search to terms/categories within that glossary (JSON string) |
| `--include-archived` | boolean | no | Include archived/deleted assets |
| `--limit` | integer | no | Max results to return (default 10, max 20) |
| `--offset` | integer | no | Pagination offset |
| `--sort-by` | string | no | Single field to sort by (JSON string) |
| `--sort-order` | string | no | Sort order |
| `--sort` | string | no | Multi-field sort (JSON string) |
| `--connection-qualified-name` | string | no | Filter by connection (e.g., default/snowflake/123) (JSON string) |
| `--tags` | string | no | Filter by Atlan tag names (JSON string) |
| `--directly-tagged` | boolean | no | Only directly tagged (not inherited) |
| `--domain-guids` | string | no | Filter by domain GUIDs. For DataProduct/DataDomain asset types, this recursively includes all sub-domains — e.g. passing a parent domain GUID returns products under that domain AND all its sub-domains at any depth. (JSON string) |
| `--date-range` | string | no | Date filters (JSON string) |
| `--guids` | string | no | Filter by specific asset GUIDs (JSON string) |
| `--term-guids` | string | no | Filter by assigned glossary term GUIDs (JSON string) |
| `--aggregations` | string | no | Aggregations to compute. Use __meanings aggregation to find which glossary terms are linked to assets. (JSON string) |
| `--count-only` | boolean | no | Return only count, no results |
| `--scroll` | boolean | no | Enable scroll mode for >10k results |
| `--include-readme` | boolean | no | Set true to fetch and return README content for each asset. Only enable when the user explicitly asks for README/documentation content — adds latency. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### traverse_lineage_tool

Traverse upstream or downstream lineage from an asset.

Returns a widget-ready graph with data assets connected by lineage edges.
Process connector nodes are bridged in the graph (A -> B instead of
A -> Process -> B); their entity data is exposed in the ``process_map``
field and each relation carries ``via_process_guids`` identifying which
ETL/transformation processes produced the connection. The lineage widget
supports progressive loading — leaf nodes show an expand button that
fetches deeper lineage on demand. Keep size small (5-15) for responsive
results; do NOT request all lineage at once.

```bash
uv run --with fastmcp python atlan_cli.py call-tool traverse_lineage_tool --guid <value> --direction <value> --depth <value> --size <value> --immediate-neighbors --offset <value> --include-attributes <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--guid` | string | yes | GUID of the starting asset |
| `--direction` | string | yes | Lineage traversal direction |
| `--depth` | integer | no | Maximum depth to traverse |
| `--size` | integer | no | Maximum number of data assets to show in the lineage graph. The widget supports progressive loading — users can click expand on leaf nodes to load more. Keep this small (5-15). Max 20. |
| `--immediate-neighbors` | boolean | no | Only return immediate neighbors (one hop) |
| `--offset` | integer | no | Pagination offset for relations (default 0) |
| `--include-attributes` | string | no | Additional attributes to include (JSON string) |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### query_assets_tool

Execute SQL queries against Atlan connections to preview data.

```bash
uv run --with fastmcp python atlan_cli.py call-tool query_assets_tool --sql <value> --connection-qualified-name <value> --default-schema <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--sql` | string | yes | SQL query to execute against the connection |
| `--connection-qualified-name` | string | yes | Qualified name of the connection to query |
| `--default-schema` | string | no | Default schema for unqualified table references (JSON string) |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### resolve_metadata_tool

Use this to search for users and groups, and to get exact usernames and group names before making updates. Also use for extra discovery on classifications, business_metadata, glossary, and data_domain_and_product when semantic_search doesn't return needed results, or before write operations to confirm exact names and GUIDs.

```bash
uv run --with fastmcp python atlan_cli.py call-tool resolve_metadata_tool --namespace-type <value> --query <value> --limit <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--namespace-type` | string | yes | Metadata namespace to search. Use 'data_domain_and_product' for BOTH data domains AND data products. |
| `--query` | string | yes | Search query - name, description, or natural language |
| `--limit` | integer | no | Max results (default 10, max 20) |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### search_atlan_docs_tool

Search Atlan's customer-facing documentation and return an LLM-generated answer with source citations. Use for how-to questions about Atlan features — not for searching data assets (use semantic_search_tool for that).

```bash
uv run --with fastmcp python atlan_cli.py call-tool search_atlan_docs_tool --query <value> --top-k <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--query` | string | yes | Question about Atlan features, how-tos, or configuration. E.g. 'How do I connect Snowflake to Atlan?' or 'How do I create a data product?' |
| `--top-k` | integer | no | Number of documentation sources to retrieve (1-10) |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### get_groups_tool

Get workspace groups and their members. Use include_members=True to list users in a group.

```bash
uv run --with fastmcp python atlan_cli.py call-tool get_groups_tool --name-filter <value> --group-id <value> --include-members --limit <value> --offset <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--name-filter` | string | no | Filter by name (partial match) (JSON string) |
| `--group-id` | string | no | Get specific group by ID (GUID) (JSON string) |
| `--include-members` | boolean | no | Include group members in response |
| `--limit` | integer | no | Maximum results (1-250) |
| `--offset` | integer | no | Pagination offset |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### get_asset_tool

Get detailed information about a single asset by its GUID or qualified name.

```bash
uv run --with fastmcp python atlan_cli.py call-tool get_asset_tool --guid <value> --qualified-name <value> --asset-type <value> --include-attributes <value> --include-dq-checks --include-readme --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--guid` | string | no | Asset GUID to retrieve (JSON string) |
| `--qualified-name` | string | no | Asset qualified name to retrieve (e.g. default/snowflake/1234/DB/SCHEMA/TABLE) (JSON string) |
| `--asset-type` | string | no | Asset type (required when using qualified_name). e.g. Table, Column, View, Database, Schema (JSON string) |
| `--include-attributes` | string | no | Additional attributes to include (JSON string) |
| `--include-dq-checks` | boolean | no | Set true to include linked data quality checks (Soda, Anomalo, Monte Carlo, Atlan native DQ rules) for this asset |
| `--include-readme` | boolean | no | Set true to fetch and return README content for the asset. Only enable when the user explicitly asks for README/documentation content — adds latency. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### update_assets_tool

Update attributes on one or more assets. Each item specifies the asset identity + fields to change. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool update_assets_tool --updates <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--updates` | string | yes | Asset update(s). Each update is a self-contained dict with asset identity (guid, name, qualified_name, type_name) plus the fields to change: user_description, certificate_status, readme, term, owner_users, owner_groups, category_guids, term_relations. Multiple attributes can be updated per asset in one call. For owner_users/owner_groups: REPLACES the full list — include existing owners to keep them. Use exact usernames from resolve_metadata. For category_guids: list of category GUIDs to assign an AtlasGlossaryTerm to (replaces existing categories). For AtlasGlossaryTerm or AtlasGlossaryCategory: also include glossary_guid (the parent glossary GUID, available as glossaryGuid in search results). For term: operation must be exactly 'append' (link terms), 'remove' (unlink terms), or 'replace' (overwrite all). Do NOT use 'add' or 'delete' — these are invalid and will fail. For term_relations (AtlasGlossaryTerm only): link one term to another using a relation type. Supported types: synonyms, antonyms, see_also (Related to), preferred_terms (Recommended), preferred_to_terms, translated_terms (Translates to), valid_values, valid_values_for, classifies, is_a (Classified by), replaced_by, replacement_terms. Each relation type takes {op, guids} where op is 'append', 'replace', or 'remove' and guids is a list of target term GUIDs. Use search_assets_tool to find GUIDs of both source and target terms before calling this tool. (JSON string) |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### create_glossaries

Create one or more glossaries in Atlan. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool create_glossaries --glossaries <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--glossaries` | string | yes | Glossary definitions (JSON string) |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### create_glossary_terms

Create one or more glossary terms in Atlan. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool create_glossary_terms --terms <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--terms` | string | yes | Term definitions (JSON string) |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### create_glossary_categories

Create one or more glossary categories in Atlan. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool create_glossary_categories --categories <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--categories` | string | yes | Category definitions (JSON string) |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### create_domains

Create one or more data domains in Atlan. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool create_domains --domains <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--domains` | string | yes | Domain definitions (JSON string) |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### create_data_products

Create one or more data products in Atlan. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool create_data_products --products <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--products` | string | yes | Product definitions (JSON string) |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### create_dq_rules_tool

Create data quality rules in Atlan. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool create_dq_rules_tool --rules <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--rules` | string | yes | DQ rule definitions. Use EXACTLY these field names: rule_type (str, REQUIRED): Null Count, Null Percentage, Blank Count, Blank Percentage, Min Value, Max Value, Average, Standard Deviation, Unique Count, Duplicate Count, Regex, String Length, Valid Values, Valid Values Reference, Freshness, Row Count, Custom SQL, Recon Row Count, Recon Average, Recon Sum, Recon Duplicate Count, Recon Unique Count. asset_qualified_name (str, REQUIRED): qualified name of the table/view. threshold_value (number, REQUIRED): threshold for the rule. threshold_compare_operator (str): EQUAL (EQ), GREATER_THAN_EQUAL (GTE), LESS_THAN_EQUAL (LTE), BETWEEN (BETWEEN), GREATER_THAN (GT), LESS_THAN (LT). alert_priority (str): URGENT, NORMAL, LOW. column_qualified_name (str): required for column-level rules. custom_sql (str): SQL query, required when rule_type is 'Custom SQL'. rule_name (str): display name, required when rule_type is 'Custom SQL'. dimension (str): required when rule_type is 'Custom SQL': COMPLETENESS, TIMELINESS, ACCURACY, CONSISTENCY, UNIQUENESS, VALIDITY, VOLUME. threshold_unit (str): PERCENTAGE, SECONDS, MINUTES, HOURS, DAYS, WEEKS, MONTHS, YEARS, ABSOLUTE. reference_dataset_qualified_name (str): required for Recon and Reference rules. reference_column_qualified_name (str): required for column-level Recon/Reference rules. description (str): optional rule description. (JSON string) |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### schedule_dq_rules_tool

Schedule data quality rule execution on assets. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool schedule_dq_rules_tool --schedules <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--schedules` | string | yes | Schedule definitions (JSON string) |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### update_dq_rules_tool

Update existing data quality rules. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool update_dq_rules_tool --rules <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--rules` | string | yes | DQ rule updates. Use EXACTLY these field names: qualified_name (str, REQUIRED): qualified name of the rule to update. rule_type (str, REQUIRED): Null Count, Null Percentage, Blank Count, Blank Percentage, Min Value, Max Value, Average, Standard Deviation, Unique Count, Duplicate Count, Regex, String Length, Valid Values, Valid Values Reference, Freshness, Row Count, Custom SQL, Recon Row Count, Recon Average, Recon Sum, Recon Duplicate Count, Recon Unique Count. asset_qualified_name (str, REQUIRED): qualified name of the table/view. threshold_value (number): new threshold value. threshold_compare_operator (str): EQUAL (EQ), GREATER_THAN_EQUAL (GTE), LESS_THAN_EQUAL (LTE), BETWEEN (BETWEEN), GREATER_THAN (GT), LESS_THAN (LT). threshold_unit (str): PERCENTAGE, SECONDS, MINUTES, HOURS, DAYS, WEEKS, MONTHS, YEARS, ABSOLUTE. alert_priority (str): URGENT, NORMAL, LOW. custom_sql (str): updated SQL query for Custom SQL rules. rule_name (str): updated display name for Custom SQL rules. dimension (str): for Custom SQL rules: COMPLETENESS, TIMELINESS, ACCURACY, CONSISTENCY, UNIQUENESS, VALIDITY, VOLUME. description (str): optional rule description. (JSON string) |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### delete_dq_rules_tool

Delete data quality rules by their GUIDs. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool delete_dq_rules_tool --rule-guids <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--rule-guids` | string | yes | GUIDs of DQ rules to delete (JSON string) |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### manage_asset_lifecycle_tool

Manage asset lifecycle: archive, restore, or permanently purge assets. WARNING: PURGE cannot be undone. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool manage_asset_lifecycle_tool --operation <value> --guids <value> --asset-type <value> --qualified-name <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--operation` | string | yes | Lifecycle operation to perform |
| `--guids` | string | no | Asset GUIDs (required for ARCHIVE/PURGE) (JSON string) |
| `--asset-type` | string | no | Asset type (required for RESTORE) (JSON string) |
| `--qualified-name` | string | no | Qualified name (required for RESTORE) (JSON string) |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### manage_announcements_tool

Add or remove announcements (information, warning, issue) on assets. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool manage_announcements_tool --asset-guids <value> --operation <value> --announcement-type <value> --title <value> --message <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--asset-guids` | string | yes | Asset GUIDs to update (comma-separated or JSON array) |
| `--operation` | string | yes | Announcement operation |
| `--announcement-type` | string | no | Announcement type (required for SET) (JSON string) |
| `--title` | string | no | Announcement title (required for SET) (JSON string) |
| `--message` | string | no | Announcement message (optional) (JSON string) |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### update_custom_metadata_tool

Update custom metadata on one or more assets. Set replace=True for full replacement, False (default) for partial update. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool update_custom_metadata_tool --updates <value> --replace --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--updates` | string | yes | Single update (dict) or batch updates (list of dicts). Each item requires: guid, custom_metadata_name, attributes. Single: {"guid": "...", "custom_metadata_name": "CM", "attributes": {"k": "v"}}. Batch: [{"guid": "g1", ...}, {"guid": "g2", ...}] (JSON string) |
| `--replace` | boolean | no | If False (default): partial update — only specified attributes are changed. If True: full replacement — ALL attributes in the CM set are replaced; unspecified attributes are cleared. replace=True only supported for single asset (dict input), not batch. |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### remove_custom_metadata_tool

Remove a custom metadata set from an asset. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool remove_custom_metadata_tool --guid <value> --custom-metadata-name <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--guid` | string | yes | GUID of the asset |
| `--custom-metadata-name` | string | yes | Name of the custom metadata set to remove |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### create_custom_metadata_set_tool

Create one or more custom metadata sets with typed attributes. Defines the schema; use update_custom_metadata to set values on assets. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool create_custom_metadata_set_tool --sets <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--sets` | string | yes | Single CM set (dict) or multiple CM sets (list of dicts). Each requires: display_name (str), attributes (list). Optional: description (str). Each attribute requires: display_name, attribute_type (string\|int\|float\|boolean\|date\|enum\|users\|groups\|url\|SQL\|long). Optional per attribute: multi_valued (bool), description (str). For enum attributes: provide enum_values (list of allowed strings) to create a new enum, OR options_name (str) to reference an existing Atlan enum. Single: {"display_name": "Data Quality", "attributes": [{"display_name": "Score", "attribute_type": "int"}, {"display_name": "Dimension", "attribute_type": "enum", "enum_values": ["Accuracy", "Completeness"]}]}. Batch: [{"display_name": "CM1", "attributes": [...]}, {"display_name": "CM2", "attributes": [...]}] (JSON string) |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### delete_custom_metadata_set_tool

Permanently delete one or more custom metadata sets and all their attribute values from assets. Irreversible. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool delete_custom_metadata_set_tool --sets <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--sets` | string | yes | Single CM set display name (string) or list of display names for batch deletion. WARNING: Irreversible — deletes the schema and all stored attribute values on assets. Single: "Data Quality". Batch: ["Data Quality", "Governance"] (JSON string) |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### add_attributes_to_cm_set_tool

Add new typed attributes to an existing custom metadata set. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool add_attributes_to_cm_set_tool --display-name <value> --attributes <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--display-name` | string | yes | Display name of the existing CM set |
| `--attributes` | string | yes | Attributes to add. Each requires: display_name, attribute_type (string\|int\|float\|boolean\|date\|enum\|users\|groups\|url\|SQL\|long). Optional: multi_valued (bool), description (str). For enum attributes: provide enum_values (list of allowed strings) to create a new enum, OR options_name (str) to reference an existing Atlan enum. Example: [{"display_name": "Risk Score", "attribute_type": "int"}, {"display_name": "Status", "attribute_type": "enum", "enum_values": ["Draft", "Approved", "Rejected"]}] (JSON string) |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### remove_attributes_from_cm_set_tool

Remove (archive) attributes from an existing custom metadata set. Archived attributes are soft-deleted and their values cleared from all assets. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool remove_attributes_from_cm_set_tool --display-name <value> --attribute-names <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--display-name` | string | yes | Display name of the existing CM set |
| `--attribute-names` | string | yes | Display name(s) of attributes to remove (archive). Archived attributes are soft-deleted: values are cleared from assets and hidden in UI. Example: ["Score", "Reviewed By"] or a JSON string of the list. (JSON string) |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### add_atlan_tags_tool

Add Atlan tags to one or more assets. Pass a dict for single asset, list for batch. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool add_atlan_tags_tool --updates <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--updates` | string | yes | Single tag addition (dict) or batch (list of dicts). Each item: {guid, tag_names, propagate (default true), remove_on_delete (default true), restrict_lineage_propagation (default false), restrict_hierarchy_propagation (default false)}. Single: {"guid": "...", "tag_names": ["PII"]}. Batch: [{"guid": "g1", "tag_names": ["PII"]}, ...] (JSON string) |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### remove_atlan_tag_tool

Remove an Atlan tag from one or more assets. Pass a dict for single asset, list for batch. Always uses propose mode — STOP after proposing and wait for user approval before executing.

```bash
uv run --with fastmcp python atlan_cli.py call-tool remove_atlan_tag_tool --updates <value> --mode <value> --user-query <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--updates` | string | yes | Single tag removal (dict) or batch (list of dicts). Each item: {guid, tag_name}. Single: {"guid": "...", "tag_name": "PII"}. Batch: [{"guid": "g1", "tag_name": "PII"}, ...] (JSON string) |
| `--mode` | string | no | ALWAYS use 'propose'. Returns a preview for user review. NEVER use 'execute' unless the user has explicitly approved. |
| `--user-query` | string | no | REQUIRED: Always pass the user's exact question/prompt that triggered this tool call. Used for tracing and observability. (JSON string) |

### get_asset_icons

Fetch SVG icons for asset types. Internal tool used by widgets.

```bash
uv run --with fastmcp python atlan_cli.py call-tool get_asset_icons --icon-names <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--icon-names` | array[string] | yes |  |

## Utility Commands

```bash
uv run --with fastmcp python atlan_cli.py list-tools
uv run --with fastmcp python atlan_cli.py list-resources
uv run --with fastmcp python atlan_cli.py read-resource <uri>
uv run --with fastmcp python atlan_cli.py list-prompts
uv run --with fastmcp python atlan_cli.py get-prompt <name> [key=value ...]
```

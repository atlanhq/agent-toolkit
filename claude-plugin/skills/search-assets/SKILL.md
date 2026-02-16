---
name: search-assets
description: Search for data assets in the Atlan catalog using natural language or structured filters. Use when users ask to find tables, columns, dashboards, or any data asset.
---

# Search Assets in Atlan

The user wants to search for data assets in Atlan. Use the available MCP tools to find what they're looking for.

## Strategy

1. **Always use semantic search** (`semantic_search_tool`) for natural language queries. This is the most flexible and user-friendly approach.

## Instructions

- If the query is natural language (e.g., "find customer tables"), use `semantic_search_tool`
- Always show results in a clear, organized format with asset name, type, description, and qualified name
- Include pagination info: "Showing X of Y total results"
- If results include custom metadata, display it clearly
- If no results found, suggest broadening the search or trying synonyms

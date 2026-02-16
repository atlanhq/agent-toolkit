---
name: explore-lineage
description: Explore data lineage to understand where data comes from (upstream) or where it flows to (downstream). Use when users ask about data sources, dependencies, impact analysis, or data flow.
---

# Explore Data Lineage

The user wants to understand data lineage. Use `traverse_lineage_tool` to trace data flow.

## Instructions

- Parse the user's intent from: `$ARGUMENTS`
- First, search for the asset if only a name is provided (use `semantic_search_tool` to find the GUID)
- Then traverse lineage using `traverse_lineage_tool` with the asset's GUID
- Use `UPSTREAM` direction to find data sources (where data comes from)
- Use `DOWNSTREAM` direction to find data consumers (where data goes)
- For impact analysis, trace downstream to show what would be affected by changes
- For root cause analysis, trace upstream to find the data origin

## Output Format

Present lineage as a clear flow:
- Show asset names, types, and connections
- Indicate the direction of data flow
- Highlight the starting asset
- If lineage is deep, summarize the key paths

## Common Patterns

- "Where does this data come from?" -> UPSTREAM traversal
- "What depends on this table?" -> DOWNSTREAM traversal
- "Show me the full pipeline" -> Both UPSTREAM and DOWNSTREAM
- "Impact analysis for X" -> DOWNSTREAM traversal

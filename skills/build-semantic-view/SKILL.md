---
name: build-semantic-view
description: Build a semantic model for Snowflake Cortex Analyst, a Databricks metric view, a Databricks Genie space or dbt MetricFlow from Atlan-governed context, and put it in this repository. Use when someone asks to build a semantic view, a semantic model, a Cortex model, a metric view, a Genie space config or a dbt semantic model for a set of tables.
---

# Build a semantic view

The `build_semantic_view_tool` does the work and its own description carries the full
sequence. This skill adds only what a terminal can do that a chat window cannot: ask the
question as a real prompt, and write the file where the person is working.

## Getting the tables

Table names must be full Atlan qualifiedNames including the connection prefix, like
`default/snowflake/1712345678/ANALYTICS/SALES/ORDERS`. The short `DB/SCHEMA/TABLE` form is
not found. If you have names but not qualifiedNames, use `search_assets_tool` to resolve
them first. Never invent one.

## Confirming before you spend the minutes

Call `build_semantic_view_tool` with `dry_run=true` first. Put its answer to the user with
**AskUserQuestion**, not as prose, so they can pick:

- **Add the suggested tables** when `suggested_tables` is non-empty. Say plainly that a
  relationship needs both of its tables in the model, so without them the model will have
  no relationships at all.
- **Build the list as it stands.**

Then call again with `dry_run=false` and the confirmed list. Relay `summary` verbatim, and
report progress while you poll.

## Where the file goes

Write the returned `content` to `./semantic_models/<name>.yaml`, or `.json` for `genie`.
Create the directory if it is missing. Tell the user the path.

- **dbt** returns several documents in one stream, separated by `# path:` banners. Split on
  those banners and write each to the path its banner names.
- **genie** returns JSON in which `_partial: true` is expected and is not a problem. A Genie
  space also needs a Databricks metric view deployed first, so build `engine=databricks`
  over the same tables as well and say the metric view is deployed before the space.

Say once, at the end, that nothing was saved to Atlan and this file is theirs to commit.

## When the tool is not available

If the tool is missing or reports that the capability is not enabled, say so and stop. Do
not fall back to writing a semantic model by hand: every element of a real one comes from
Atlan's catalog, and an invented one looks identical and is wrong.

## Fixing what is missing

When the summary reports undescribed columns or no relationships, the fix belongs in Atlan
so every future build inherits it. Use the **update-to-atlan** skill.

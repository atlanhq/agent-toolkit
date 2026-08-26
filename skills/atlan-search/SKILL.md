---
name: atlan-search
description: How to find things in the Atlan data catalog with the Atlan MCP tools — which of semantic_search / search_assets / get_assets / traverse_lineage / resolve_metadata / get_users to reach for, and the filter rules that make each one return the right answer. Use for any discovery ask over catalog metadata — "what data do we have about X", "which table has Y", "find verified Snowflake tables owned by Z", "how many dashboards per domain", tags and custom metadata, glossary terms, domains and data products, data quality checks, lineage, BI and pipeline assets, and counts or breakdowns of any of these. Not for querying row-level data values (use query_assets) and not for skills / knowledge files / agents (use read_artifact).
---

# Searching the Atlan catalog

The catalog holds *metadata* — assets, their names, owners, certification,
tags, glossary links, domains, quality checks, lineage. It does not hold row
values. Pick the entry point from the ask, then apply the rules below.

## Pick the tool

| The ask | Tool |
|---|---|
| Topic / natural-language discovery — "what data do we have about churn", "which table has retention rate" | `semantic_search` |
| Counts and breakdowns — "how many verified tables", "assets by connector" | `search_assets` with `return_count_only` / `aggregations` |
| Exact, deterministic attribute filters — name prefix, certification, connector, type, tag, domain, term | `search_assets` |
| Full detail on assets you already have GUIDs for — columns, README, custom metadata values | `get_assets` |
| Upstream / downstream dependencies | `traverse_lineage` (resolve the GUID first) |
| Data quality checks and rules | `search_assets` on the DQ types — see `references/data-quality.md` |
| Which tags or custom-metadata sets exist on this tenant | `resolve_metadata` |
| A person or a team | `get_users` / `get_groups` |
| Which attributes a type supports | `describe_asset_type` |
| Row-level data values in the source warehouse | `query_assets` |
| Skills, knowledge files, agents (context repos) | `read_artifact` |
| How a product feature works | `search_atlan_docs` |

`semantic_search` has its own planner: it reads the whole question, decomposes
it, and applies filters itself. `search_assets` does exactly what you tell it
and nothing more. Reach for `semantic_search` when the ask is phrased as a
question; `search_assets` when you already know the precise filter.

## The rules that decide whether you get the right answer

**1. Be precise about asset type.** "tables" means `asset_type="Table"` — not
Views, not Columns. "dashboards" means the BI dashboard types. `asset_type` is
singular and takes either a string or a list (`["Table", "View"]`). Only go
broad when the user says "all assets", and when you do, exclude the internal
plumbing types (see `references/filters.md`).

**2. Never report absence from one narrow search.** The same table name often
exists in several connectors, and a filter you added yourself can hide the
answer. Widen once, then say what you actually checked.

**3. Archived assets are excluded by default.** Leave `include_archived=false`
unless the user asks about deleted assets.

**4. Read the right name and description fields — and request them.** Label an
asset by `displayName` when set, else `name` — `name` is the technical
identifier (`DIM_BEVERAGE_ORDER_CUSTOMER`), `displayName` is what a
human curated ("Beverage Orders"). For descriptions, prefer in this order:
`userDescription` → AI-generated description → `description` (source-system).
They are separate fields, not coalesced — and none of them come back unless
you ask. Default `attributes` for any asset you intend to describe:

```json
["displayName", "name", "userDescription", "description", "certificateStatus", "connectorName"]
```

**5. "Top", "most used", "popular" means `sort` on `popularityScore`
descending.** It is also a good tiebreaker when several assets share a name.
For "biggest" / "most rows", sort on the numeric attribute itself
(`rowCount`, `sizeBytes`, `columnCount`) — popularity is not size.

**6. Tags and custom metadata are not `conditions`.** Atlan tags go in the
`tags` parameter. Custom metadata needs the set's exact display name, which
you get from `resolve_metadata` first. Glossary terms go in
`assigned_term_guids`, domains in `domain_guids`. Relationship attributes
(`meanings`, `atlanTags`, `parentCategory`, `seeAlso`) are not searchable as
conditions at all.

**7. Columns go both ways.** A table's columns come from the table:
`get_assets(guid=…, attributes=["columns"])` — not from a column search. But
"which table has a `customer_email` column?" is the reverse: search
`asset_type="Column"` on the column name, then read the parent from each hit's
`tableName` / `qualifiedName` and pivot to that table.

**8. Counting is a different call than listing.** `search_assets` with
`return_count_only=true` gives the uncapped total; `aggregations` gives a
breakdown. A `limit=100` page is not a count.

**9. Resolve a GUID before any tool that needs one.** `get_assets` and
`traverse_lineage` take GUIDs from a prior search result — never a
qualifiedName, never an invented one.

**10. Get the call shape right.** These fail on every tenant:

- The natural-language parameter is `user_query`. Not `query`, `search_query`,
  `query_text`, or `semantic_query`.
- `conditions` / `any_conditions` / `negative_conditions` are JSON objects,
  not strings. Do not pass a serialized blob.
- There is no `filters` parameter. Attribute filters go in `conditions`.
- `limit` is 1–100 on search tools (lineage `limit` is max 20).
- `direction` on `traverse_lineage` is `UPSTREAM` or `DOWNSTREAM`. There is no
  `BOTH` — run it twice and merge.
- One field, several possible values, is a `within` list — never `name`,
  `name2`, `name3` (that errors), and never one call per value:
  `{"name": {"operator": "within", "value": ["ORDERS", "ORDER_ITEMS"]}}`

**11. Split a compound ask before you filter.** "who owns
`db.schema.TABLE` and is it tagged PII?" is three steps: resolve the asset,
then read `ownerUsers` / `ownerGroups` / tags off it via `get_assets`
attributes. Ownership and tags are not expressible as one condition — see
rule 6.

**12. Not every question is a catalog question.** The catalog holds metadata
about assets. Bulk metadata export, "what does this company do", vendor and
tooling questions, and product how-tos are not searches — say so and point at
`search_atlan_docs` or the right team instead of returning a bad match.

## References

Load only the one the ask needs.

| File | Covers |
|---|---|
| `references/filters.md` | `search_assets` condition cookbook — operators, type lists, internal-type exclusions, tags, custom metadata, dates, aggregations |
| `references/lineage.md` | Resolving the right asset instance, then traversing |
| `references/glossary.md` | Terms, categories, glossaries, category hierarchy, linked assets |
| `references/data-products.md` | Domains, subdomains, products, ports, lifecycle status |
| `references/data-quality.md` | Atlan native DQ rules plus Soda, Anomalo, Monte Carlo |
| `references/bi-and-pipelines.md` | Dashboards, reports, workbooks; Airflow, dbt, Fivetran, ADF |

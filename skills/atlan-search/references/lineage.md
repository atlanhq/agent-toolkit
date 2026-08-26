# Lineage

`traverse_lineage` needs a GUID. Most lineage answers go wrong in the
*resolution* step, not the traversal.

## Resolve the right instance first

The same table name commonly exists in several connectors — Snowflake,
Databricks, Redshift — and only some of them have lineage tracked.

1. Search for the name: `semantic_search("FACT_ORDERS")`, or
   `search_assets` with `{"name": "FACT_ORDERS"}` and `asset_type="Table"`.
2. Look at **every** hit, not the first. Ask for `hasLineage`,
   `connectorName`, `qualifiedName`, `popularityScore` in `attributes`.
3. Keep the ones with `hasLineage=true`. If the user named a connector,
   database, or schema, use it to disambiguate. Otherwise take the highest
   `popularityScore`.
4. If none has lineage, say so — and say how many instances you checked. Never
   report "no lineage" after looking at one hit.

## Traverse

`traverse_lineage(guid=…, direction="upstream" | "downstream")`.

**One hop by default.** `immediate_neighbors=true` is the default, and `depth`
is ignored while it is set. Nothing in the response flags that the traversal
stopped at one hop — `has_more` stays false either way. For anything spanning
more than direct parents or children, pass `immediate_neighbors=false` and set
`depth` explicitly.

- "what's upstream of this table?" — one hop is fine
- "where does this data originate?", "does this feed the exec dashboard?",
  "what breaks if we drop this column?" — `immediate_neighbors=false`,
  `depth=5` or more

Keep `limit` small — 5 to 15 (default 10, max 20). The response is a
widget-ready graph and the lineage widget loads deeper levels on demand when
the user expands a leaf. Requesting a whole graph at once is slow and usually
unread.

## Reading the result

- Data assets are the nodes; edges connect them directly.
- Transformation processes are **bridged out** of the graph — `A -> B` rather
  than `A -> Process -> B`. The process entities live in `process_map`, and
  each relation carries `via_process_guids` pointing at the ETL /
  transformation steps that produced it. Look there for the SQL or job that
  explains an edge.
- Column-level nodes are filtered out of the asset graph.

## Related

"Which assets does this dbt model feed?" is a lineage question, not a search
one. "Which pipelines exist?" is a search question — see
`bi-and-pipelines.md`.

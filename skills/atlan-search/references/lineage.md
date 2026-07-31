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

Keep `size` small — 5 to 15. The response is a widget-ready graph and the
lineage widget loads deeper levels on demand when the user expands a leaf.
Requesting a whole graph at once is slow and usually unread.

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

# BI assets and pipelines

## BI

"Dashboards" and "reports" are per-vendor types, not one generic type. Name
the ones that match the user's tooling:

| Vendor | Types |
|---|---|
| Power BI | `PowerBIDashboard`, `PowerBIReport`, `PowerBIDataset`, `PowerBITable`, `PowerBITile` |
| Tableau | `TableauDashboard`, `TableauWorkbook`, `TableauWorksheet` |
| Looker | `LookerDashboard`, `LookerLook`, `LookerExplore` |
| Sigma | `SigmaWorkbook`, `SigmaPage`, `SigmaDataElement` |
| Qlik, ThoughtSpot, Metabase, Mode, … | same pattern — `<Vendor><Object>` |

If the user says "dashboards" without naming a vendor, pass the dashboard types
for every BI connector on the tenant, or let `semantic_search` decide from the
plain-language question.

Hierarchy fields worth requesting: workspace, project, folder, and site
qualifiedNames. Use `describe_asset_type` for the exact camelCase names of a
given vendor's type.

BI assets often have **no column-level children** — Salesforce, Power BI,
Tableau, and Sigma may not expose columns the way a warehouse table does. A
zero-column result for a BI asset is normal, not a failure; check the
connector before reporting it as missing metadata.

## Pipelines and ETL

| Tool | Types |
|---|---|
| Airflow | `AirflowDag`, `AirflowTask` |
| dbt | `DbtModel`, `DbtSource`, `DbtTest` |
| Fivetran | `FivetranConnector` |
| Azure Data Factory | `AdfPipeline` |
| Matillion, Dagster, Informatica, … | same `<Tool><Object>` pattern |

"What does this pipeline read and write?" is a **lineage** question, not a
search one — resolve the pipeline asset, then `traverse_lineage` in both
directions. See `lineage.md`.

"Which pipelines exist / how many per tool?" is a search question — filter on
the pipeline types and aggregate on `connectorName` or `__typeName`.

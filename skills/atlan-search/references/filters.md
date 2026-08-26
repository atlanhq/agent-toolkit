# `search_assets` filter cookbook

`conditions` are ANDed. Each value is a literal (exact match) or an
`{operator, value}` object. Field names accept camelCase or snake_case.

```json
{"name": "customers"}
{"name": {"operator": "startswith", "value": "dim_"}}
{"name": {"operator": "contains", "value": "customer"}}
{"certificate_status": "VERIFIED"}
```

Other slots, because they are *not* `conditions`:

| Slot | Use for |
|---|---|
| `negative_conditions` | exclusions — same format (`{"name": {"operator": "contains", "value": "test"}}`) |
| `any_conditions` + `min_matches` | OR-style (`{"owner_users": "alice", "owner_groups": "analytics"}`) |
| `tags` (+ `directly_tagged`) | Atlan tags / classifications |
| `assigned_term_guids` | assets linked to a glossary term |
| `domain_guids` | assets in a data domain |
| `glossary_qualified_name` | scope term/category search to one glossary |
| `connection_qualified_name` | scope to one connection |
| `date_range` | created/updated windows |
| `guids` | fetch a known set |
| `aggregations` | breakdowns / group-by |
| `return_count_only` | uncapped total instead of a page |
| `sort` | ordering, e.g. `popularityScore` desc |
| `attributes` | which fields come back |

`limit` maxes at 100 per page; use `offset` to page.

## Certification

`certificate_status` is `VERIFIED`, `DRAFT`, or `DEPRECATED`. "Trusted",
"certified", "production-ready" all mean `VERIFIED`. Exclude deprecated
explicitly when the user wants usable assets:

```json
{"conditions": {"asset_type": "Table"},
 "negative_conditions": {"certificate_status": "DEPRECATED"}}
```

## Asset types

Be exact. Common ones:

- Relational: `Table`, `View`, `MaterialisedView`, `Column`, `Schema`,
  `Database`, `Function`, `Procedure`
- Glossary: `AtlasGlossary`, `AtlasGlossaryTerm`, `AtlasGlossaryCategory`
- Mesh: `DataDomain`, `DataProduct`
- Quality: `DataQualityRule`, `DataQualityRuleTemplate`, `SodaCheck`,
  `AnomaloCheck`, `MCMonitor`
- BI: `PowerBIDashboard`, `PowerBIReport`, `PowerBIDataset`,
  `TableauDashboard`, `TableauWorkbook`, `TableauWorksheet`,
  `LookerDashboard`, `LookerLook`, `SigmaWorkbook`, `SigmaPage`
- Pipelines: `AirflowDag`, `AirflowTask`, `DbtModel`, `DbtSource`,
  `FivetranConnector`, `AdfPipeline`

Any valid Atlan type is accepted, including niche ones (`PowerBITile`,
`LookerTile`). If unsure which attributes a type carries, ask
`describe_asset_type`.

## Going broad: exclude the plumbing

Only when the user genuinely means "all assets". These types exist for
internal bookkeeping and are noise in any user-facing list — exclude them via
`negative_conditions` on `__typeName`, or better, name the types you do want:

`Process`, `BIProcess`, `DbtProcess`, `DbtColumnProcess`, `ColumnProcess`,
`ConnectionProcess`, `MatillionComponent`, `ModelVersion`,
`FlowDatasetOperation`, `FlowFieldOperation`, `FlowControlOperation`,
`FabricVisual`, `FabricDataflowEntityColumn`, `FabricSemanticModelTable`,
`FabricSemanticModelTableColumn`, `SnowflakeTag`, `DbtTag`, `BigqueryTag`,
`DatabricksUnityCatalogTag`, `SourceTag`, `TagAttachment`, `Tag`,
`MCIncident`, `AnomaloCheck`, `BusinessPolicy`, `BusinessPolicyException`,
`BusinessPolicyIncident`, `BusinessPolicyLog`, `Cloud`, `AWS`, `Azure`,
`Google`, `DataSet`, `Infrastructure`, `Incident`, `Namespace`, `Form`,
`Response`, `Task`, `Workflow`, `WorkflowRun`, `ProcessExecution`,
`AppWorkflowRun`, `Folder`, `Resource`, `Badge`, `Link`, `Readme`,
`ReadmeTemplate`, `Semantic`, `SemanticModel`, `SemanticDimension`,
`SemanticEntity`, `SemanticField`, `SemanticMeasure`, `DataContract`,
`DataMesh`, `Stakeholder`, `Insight`, `Notebook`, `AssetGrouping`,
`AssetGroupingCollection`, `AssetGroupingStrategy`

`Procedure` is only meaningful on `snowflake` and `mssql` connections;
elsewhere it is noise.

## Tags

Discover what exists with `resolve_metadata(namespace_type="classification")`,
then filter:

```json
{"asset_type": "Table", "tags": ["PII"]}
```

`directly_tagged` defaults to `true` — direct tags only, tags inherited by
propagation excluded. Pass `directly_tagged=false` to include propagated tags,
which is usually what a governance or compliance question means — be explicit
about which you used.

## Custom metadata

Custom metadata is not a standard attribute and users rarely call it by name.
The tell is a property you do not recognise as a built-in field: "product
score", "readiness status", "risk level", any rating that is not
`popularityScore`, any status that is not `certificate_status`.

1. `resolve_metadata(namespace_type="business_metadata")` → the set's exact
   display name.
2. Pass that display name in `attributes` — e.g. `attributes: ["Stewardship"]`.
   Never pass the literal string `"customMetadata"`.

## Owners

Owner fields hold usernames (`alice.chen`), not display names ("Alice Chen").
Resolve first with `get_users`, then filter on `owner_users`. Use
`any_conditions` when either a user or their group counts:

```json
{"any_conditions": {"owner_users": "alice.chen", "owner_groups": "analytics"},
 "min_matches": 1}
```

"Unowned" assets are the negative case — check both `owner_users` and
`owner_groups` are empty before calling an asset unowned.

## Counts and breakdowns

- Total, uncapped: `return_count_only=true`.
- Grouped: `aggregations`, e.g. count by `connectorName`, `certificateStatus`,
  `__typeName`, or `ownerGroups`.
- For a plain-language "how many X by Y", `semantic_search` handles the
  decomposition itself — prefer it over hand-building aggregations.

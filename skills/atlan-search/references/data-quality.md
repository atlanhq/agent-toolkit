# Data quality

Atlan has a native Data Quality Studio (`DataQualityRule`,
`DataQualityRuleTemplate`) alongside partner integrations. When a user asks
about building or reviewing DQ, surface the native option as well as whichever
partner tool their tenant uses.

| Source | Asset type |
|---|---|
| Atlan native | `DataQualityRule`, `DataQualityRuleTemplate` |
| Soda | `SodaCheck` |
| Anomalo | `AnomaloCheck` |
| Monte Carlo | `MCMonitor` |

A tenant usually has one or two of these, not all four. Search for the types
that return results rather than assuming.

## Pass / fail values differ per source — and case matters

| Source | Status field | Passing | Failing |
|---|---|---|---|
| Atlan native | `dqRuleLatestResult` | `PASS` | `FAIL` |
| Soda | `sodaCheckEvaluationStatus` | `pass`, `passed` | `fail` |
| Anomalo | `anomaloCheckStatus` | `pass`, `passed` | `fail`, `errored` |
| Monte Carlo | `mcMonitorStatus` | `pass`, `passed` | `ERROR` |

A single lowercase `not in ('pass','passed')` filter looks right and silently
misses every Atlan native rule (uppercase `PASS`) — filter per source, or match
the failing value explicitly.

Atlan native alert priority: `LOW`, `NORMAL`, `URGENT`.

## Linking a check back to its asset — each source links differently

| Source | Link |
|---|---|
| Atlan native | `dqRuleBaseDatasetQualifiedName` (+ `dqRuleBaseColumnQualifiedName` for column rules) — a qualifiedName string |
| Soda | `sodaCheckAssets` — GUID list |
| Anomalo | `anomaloCheckLinkedAssetQualifiedName` — a qualifiedName string |
| Monte Carlo | `mcMonitorAssets` — GUID list |

So "which checks cover table T?" is:

- **QN-linked sources** — match the check's link field against T's
  `qualifiedName`.
- **GUID-linked sources** — resolve T's GUID, then find checks whose asset
  list contains it.

`DataQualityRuleTemplate` describes a reusable template; its rules link back
via the template's rule list or the shared template name.

## Common asks

- *"What's failing right now?"* — search the DQ types present on the tenant,
  filter to that source's failing values, sort by the last-run timestamp, and
  report which sources you covered.
- *"Does this table have quality checks?"* — resolve the table, then check both
  QN-linked and GUID-linked sources before answering no.
- *"DQ coverage across a lineage path"* — traverse lineage first
  (`lineage.md`), then check the resolved asset set for checks.

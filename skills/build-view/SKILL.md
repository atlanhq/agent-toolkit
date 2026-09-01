---
name: build-view
description: >
  Builds a Snowflake Cortex / Databricks Genie semantic model for a stated
  use-case from a given table list, using Atlan-governed context (descriptions,
  business rules, joins, glossary), and returns it. It does NOT author semantic
  meaning with the LLM — every element of the model comes from a concrete Atlan
  artifact. It does NOT deploy or evaluate: those are separate steps the caller
  drives if needed. Trigger phrases: "build a semantic view", "build a view for
  <use-case>", "build the semantic model from these tables".
---

# build-view — governed semantic-model build

You turn `{use_case, tables[], engine}` into a governed semantic model whose
every dimension, metric, filter, relationship, and instruction traces to an
Atlan artifact. The LLM's role is discovery/selection only — it never writes the
semantic content. That grounding is the value: the model is as good as the
governed context.

Scope is deliberately narrow: **this skill builds and returns the model.**
Deploying it, evaluating it, and diagnosing gaps are separate concerns — the
caller invokes them (or asks for them in the prompt) when needed. Do not deploy
or eval here.

## Phase 1 — Resolve inputs

- `tables[]` — the Atlan **`qualifiedName`** of each table, **including the
  connection prefix** — i.e.
  `default/snowflake/<connectionId>/<DATABASE>/<SCHEMA>/<TABLE>`, NOT the
  short `<DATABASE>/<SCHEMA>/<TABLE>` form (the short form fails with a 404).
  **Required.** If missing or ambiguous, ask — never invent a table list.
  - **Close the join set.** A relationship renders only when **both** ends of a
    join are in `tables[]`. Picking tables by importance/density usually drops the
    reference/dimension tables your facts join to, and you get a joinless model with
    nothing in the output signalling anything is missing. Include those referenced
    dimension tables. (Filters need only their own table; relationships need both ends.)
  - **At most 50 tables per build.** The endpoint caps the list in its request schema,
    so 51+ is refused with a 422 before any build starts. Split the list, or narrow it
    to the use case.
- `engine` — which form to return. Ask if not implied; they are not
  interchangeable, and a plausible-looking file for the wrong engine will not deploy:
  - `cortex` — Snowflake Cortex Analyst semantic model (`snowflake` is accepted too).
  - `genie` — the Databricks Genie space config. It carries only the cross-table
    extras (joins, verified answers, filters, instructions, synonyms); table and
    column identity are filled at deploy. So **a small or near-empty config is
    normal**, not a failed build — on a tenant with no observed joins and no analyst
    questions every section is legitimately empty. The render always stamps
    `_partial: true` and the endpoint returns a warning saying so. Report that
    warning; it is not an error, and it does **not** mean anything is missing from
    the build — the marker is unconditional.
  - `databricks` — the Databricks metric view, rendered as a deployable bundle
    (`metric_view.yaml` plus the `metric_view.deploy.yaml` a deploy actually reads).
    **A Genie space needs this deployed first.** The Genie config's `metric_view_fqn`
    is supplied at deploy time from the catalog / schema / view of a metric view that
    already exists in Databricks, so end to end the order is: build the metric view →
    deploy it → build the Genie config → deploy the space. If the target is Genie,
    ask for **both** engines.

  The two BUILDS are independent — asking for `databricks` first does not change the
  `genie` output — but the DEPLOYS are ordered, because the space can only point at a
  metric view that already exists.
  - `dbt` — dbt semantic model; validates offline against `dbt-semantic-interfaces`,
    the suite dbt-core and MetricFlow run.
- `use_case` — labels intent; carried into naming/description.

## Phase 2 — Build via the companion script

Run the bundled companion — **`${CLAUDE_PLUGIN_ROOT}/skills/build-view/build_model.py`** —
never improvise the HTTP call. The script owns the endpoint, auth header, timeout,
and error handling so the build is deterministic:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/build-view/build_model.py \
  --tables @tables.json --engine <cortex|databricks|genie|dbt> --name <use_case> --out model.yaml
```

It POSTs `{tables, engine, name}` to the governed `/semantic-model/build`
(store-nothing) endpoint and writes the returned model YAML to `--out`. Endpoint
resolution: `--endpoint` › `$ATLAN_BUILD_ENDPOINT`. **One of the two is required** —
there is no baked-in default, and the script exits telling you so. Auth is automatic:
it sends
`Authorization: Bearer $ATLAN_API_KEY` when set (the hosted endpoint requires it;
the mock ignores it). Do **NOT** use any superseded "generate" path.

The build reads columns, descriptions, business rules (custom instructions),
joins, and glossary from Atlan's catalog. No LLM authoring happens.

**It blocks, and build time grows with the table count.** The script's default
timeout is 1200s. If you run it from a shell tool, raise that tool's timeout to match
— do not accept a 120s default, and do not background it (a backgrounded call loses
the YAML).

**Read the exit as one of three outcomes.** Do not hand-author a model in any of
them.

- **No model** — the script exits non-zero and no file is written (bad engine, no
  tables, every table failed, assembly failed). STOP and surface its message.
- **PARTIAL** — exits non-zero, *and the model is on disk*: some tables did not model
  and the script names each one with its reason. The model covers the rest and is
  deployable for those tables. Surface the failed tables and let the caller decide
  whether to proceed or fix the list — do not silently treat it as clean.
- **REJECTED** — exits non-zero with the model on disk, but the target engine's own
  validator refused the file (`validation: invalid`). This is **not** a partial build:
  the model is whole and **will not deploy**. Never present it as usable. Surface the
  engine's error verbatim.

`validation: skipped` is NOT a failure (no engine was reachable to compile-check) —
the script carries the model forward and says so. `invalid` is the only validation
status that is fatal.

## Phase 3 — Return the model

Hand back the `--out` path with a one-line summary (engine + table count from the
script's output). Nothing else — no deploy, no gap analysis.

## Style rules

- Zero LLM authoring of semantic meaning. Every element maps to an Atlan
  artifact; if Atlan can't supply something, leave it out — do not invent it.
- Prefer the governed build path; if a tool/endpoint is unavailable, STOP and
  say so — don't substitute a different builder silently.
- Never log secrets or credential values.

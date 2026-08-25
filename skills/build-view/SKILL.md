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

- `tables[]` — fully-qualified table identifiers to model. **Required.** If
  missing or ambiguous, ask — never invent a table list.
- `engine` — `cortex` | `genie` | `databricks`. Ask if not implied.
- `use_case` — labels intent; carried into naming/description.

## Phase 2 — Build via the companion script

Run the bundled companion — **`${CLAUDE_PLUGIN_ROOT}/skills/build-view/build_model.py`** —
never improvise the HTTP call. The script owns the endpoint, auth header, timeout,
and error handling so the build is deterministic:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/build-view/build_model.py \
  --tables @tables.json --engine <cortex|genie|databricks> --name <use_case> --out model.yaml
```

It POSTs `{tables, engine, name}` to the governed `/semantic-model/build`
(store-nothing) endpoint and writes the returned model YAML to `--out`. Endpoint
resolution: `--endpoint` › `$ATLAN_BUILD_ENDPOINT` (override, e.g. the local mock)
› the script's baked-in hosted default. Auth is automatic: it sends
`Authorization: Bearer $ATLAN_API_KEY` when set (the hosted endpoint requires it;
the mock ignores it). Do **NOT** use any superseded "generate" path.

The build reads columns, descriptions, business rules (custom instructions),
joins, and glossary from Atlan's catalog. No LLM authoring happens.

**It blocks (real builds take 4–5 min); the script's default timeout is 400s.** If
you run it from a shell tool, raise that tool's timeout to match — do not accept a
120s default, and do not background it (a backgrounded call loses the YAML).

**On failure the script exits non-zero with the HTTP code (never the credential)
— STOP and surface it.** Do not hand-author a model to keep going. `validation:
skipped` is NOT a failure (no engine was reachable to compile-check) — the script
carries the model forward and says so.

## Phase 3 — Return the model

Hand back the `--out` path with a one-line summary (engine + table count from the
script's output). Nothing else — no deploy, no gap analysis.

## Style rules

- Zero LLM authoring of semantic meaning. Every element maps to an Atlan
  artifact; if Atlan can't supply something, leave it out — do not invent it.
- Prefer the governed build path; if a tool/endpoint is unavailable, STOP and
  say so — don't substitute a different builder silently.
- Never log secrets or credential values.

---
name: update-to-atlan
description: >
  Persists a proven context fix back to Atlan so it's reused by every future
  build, consumer, and engine — closing the loop from "fix that helped the eval"
  to "governed context in the system of record". Given ONE typed context diff
  (filter / relationship / description / glossary_term / popular_query), it routes
  to the correct Atlan write tool, gates on explicit human approval (the write
  tools execute immediately — there is no propose mode), writes, and verifies by
  reading the entity back. ALWAYS use this skill for ANY intent to persist, push,
  write, or save context BACK to Atlan — never improvise that write inline with
  ad-hoc MCP/Bash calls. Trigger phrases: "persist this fix to Atlan", "persist
  this filter/relationship/term context fix back to Atlan", "push this back to
  Atlan", "push this filter/relationship/term back to Atlan", "write the context
  fix back", "write the fix back to Atlan", "update the context in Atlan", "save
  this fix to Atlan". Fires even when no concrete diff is in context yet — in
  that case it ASKS the user for the typed diff rather than declining.
---

# update-to-atlan — the write-back hand

Turn one proven context fix (from assess-gap, or supplied) into durable governed
context in Atlan — the plugin's value: a one-off patch becomes reusable context.

## Phase 1 — Map the fix to a write, then call the script

On any intent to persist a fix **back to Atlan**, this skill owns it. Take the
**one typed diff** (use assess-gap's output verbatim; if none is in context, ask
for it — never invent one). Map it to a `--type` and run the bundled script:

```
${CLAUDE_PLUGIN_ROOT}/skills/update-to-atlan/atlan_writeback.py write --type <T> --payload @<file>
```

| Fix | `--type` | Atlan asset | payload |
|---|---|---|---|
| description | `description` | asset `userDescription` (dbt `description` untouched) | `{asset_qn, user_description}` |
| glossary term | `glossary_term` | `AtlasGlossaryTerm` (+ optional column edge) | `{name, glossary_qn\|glossary_guid, [description], [assign_column_qn]}` |
| filter | `filter` | `SqlInsightFilter` | `{dataset_qn, column_qn, predicate_sql, name, when_to_use}` |
| relationship | `relationship` | `SqlInsightJoin` | `{source_dataset_qn, joined_dataset_qn, join_type, cardinality, name, column_pairs:[{source_column_qn, joined_column_qn}]}` |
| popular query | `popular_query` | `SqlInsightBusinessQuestion` | `{dataset_qn, question, sql, name}` |

The script owns everything operational — auth (`ATLAN_*` env), the Cloudflare
User-Agent, guid resolution, the right endpoint per type, and read-back — and it
**raises on anything wrong** (missing env, HTTP error), so don't pre-check those;
surface its error if it fails. Notes: a **metric** is not a write type — persist
its definition as a `glossary_term`, its calculation stays in the model. Always
use the `${CLAUDE_PLUGIN_ROOT}/…` path (the skill's cwd is the user's workspace),
and route every write through this script — never improvise via MCP/Bash.

## Phase 2 — Gate on approval, then write

The write executes immediately (no dry-run). Present the diff, its target
`qualifiedName`, and the value to be set; write **only** what the user approves.
Then run `write` — it read-back-verifies and prints `{guid, status, verbatim_ok}`.
To revert: `atlan_writeback.py delete --guid <g> --hard`.

## Phase 3 — Report

What landed (type, target, guid, value) and what didn't (declined, or the script's
error verbatim). Persisted context is picked up by future builds/consumers on
Atlan's sync cadence; it does not need to re-enter the current in-session model.

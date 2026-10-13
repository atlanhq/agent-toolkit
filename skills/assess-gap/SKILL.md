---
name: assess-gap
description: >
  Diagnoses WHY a semantic view is failing its evals and proposes grounded,
  typed context fixes — the "map" for turning a red eval into a specific,
  defensible change to the model. Runs after build+deploy+eval in the
  talk-to-data loop: it reads only the SAFE eval projection (never the
  golden answers), classifies each failure against a fixed gap taxonomy,
  and emits one grounded diff per gap that the fix step applies and the
  update-to-atlan skill persists to Atlan. This is the field-team framework
  for "how do I read a failing eval and know what context is missing?"
  Trigger phrases: "assess the gap", "why is my semantic view failing",
  "diagnose the eval failures", "what context is missing", "improve my
  semantic view against the evals", "hillclimb the model".
---

# assess-gap — read the failures, name the missing context

You are the **gap-assessment** step of the eval-driven talk-to-data loop:
`build → deploy → eval → **assess-gap** → fix → re-eval → update-to-atlan`.
Your job is NOT to answer the questions. It is to explain, for each failing
eval case, **what context the model was missing that made the agent generate
the wrong SQL**, and to propose exactly one grounded fix per gap.

Two non-negotiables define this skill:

1. **You never see the golden answers.** You diagnose only from what the agent
   *did* (its generated SQL / answer / verdict) versus the model it *had*. The
   correct answers are firewalled out of your inputs on purpose (see Phase 1).
   Diagnosing against the oracle is teaching-to-the-test; it produces fixes that
   pass the eval and fail in production. Refuse to proceed if goldens leak in.
2. **Every fix is grounded in the model.** Each proposed `expr`/column MUST
   appear verbatim in the current semantic model. You never invent a table,
   column, or join. If you cannot ground a fix, you say so — you do not guess.

## Phase 1 — Resolve inputs and prove the firewall

Gather, from the loop's working directory (take these as inputs; never hardcode
a dataset, run-id, or path):

- **the safe eval projection** — one record per case with
  `{case_id, question, engine, verdict, cortex_sql | generated_sql, answer}`.
  It MUST NOT contain any of `golden_result`, `golden_value`, `golden_sql`,
  `judge_reason`. If any of those keys is present, **STOP** and surface it: the
  file is not a safe projection and reading it would leak the oracle. (The
  reference harness enforces this in `read_traces.load_safe()`, which hard-aborts
  on those sealed keys — cite that mechanism; do not re-implement a weaker one.)
- **the current model structure** — names only: per table its
  `dimensions / time_dimensions / facts / existing filters {name, expr} /
  relationships {left, right, on}`. This is your grounding vocabulary.
- **the engine** — `cortex` or `genie` (or `databricks`). Do not assume Cortex;
  the gap classes below are engine-neutral, but the fix vocabulary must match.
- **the accuracy target** (Y%) and the iteration budget (1–2), for the caller's
  stop condition.

If there is no eval run yet, hand back to the eval step to produce one first.

## Phase 2 — Read only the failures

Select cases with `verdict ∈ {mismatch, partial, abstain}` **and** no
answer/deploy error (a compile/deploy failure is a build problem, not a context
gap — route those back to build/deploy, don't diagnose them here). For each,
you now have: the question, the SQL the agent generated, and the verdict. That
triplet — question vs. generated SQL vs. available model — is the entire basis
for diagnosis.

## Phase 3 — Classify the gap (THE MAP)

For each failing case, match the tell to exactly one gap class. This taxonomy is
the framework — state the class you chose out loud, so the reasoning is legible
and teachable, not a black box.

Every persistable fix routes through the `update-to-atlan` skill
(types: `description`, `glossary_term`, `filter`, `relationship`, `popular_query`).
A fix whose value lives in the semantic model itself (a metric's calculation, a
verified query, a time dimension) is **not** a separate Atlan asset — apply it to
the model and say so; do not force it into a writeback type.

| # | Diagnostic tell (what the generated SQL shows) | Gap class | Fix (typed diff) | Persists to Atlan as |
|---|---|---|---|---|
| 1 | Queried a rollup/summary/wrong table, or the wrong grain (e.g. `SUM` over a pre-aggregated table when the question is per-entity) | **Wrong table / grain** | `description` disambiguating the tables (a true grain metric = a calc that stays in the model) | `description` (write-back type) |
| 2 | Right table, but no `WHERE` (or the wrong one) for the business subset the question names ("open", "active", "S2+", "at-risk") | **Missing subset** | `filter` — a named, reusable predicate | `filter` → `SqlInsightFilter` |
| 3 | Needed two tables but couldn't join them (picked one, or produced a cross-join / duplicate counts) | **Missing relationship** | `relationship` — the join key | `relationship` → `SqlInsightJoin` |
| 4 | Abstained / asked for clarification, or grabbed the wrong column for a business term ("well-worked", "AI-ready", "our accounts") | **Vocabulary gap** | `glossary_term` binding the term to the column (synonyms carried in the term description — no structured-synonym attribute in the write path) | `glossary_term` → `AtlasGlossaryTerm` (+ column `meanings` edge) |
| 5 | Wrong point-in-time or window (used all-time when the question is "right now", or the wrong date column) | **Temporal logic** | a `verified_query`/`time_dimension` in the model; if a governed window exists, a `description` naming it | model-only (no Atlan asset), or a `description` write-back |

Rules for classification:
- Prefer the table the **question** is really about, not the one the agent
  wrongly used. The most common failure is class 1 → the fix is often to make
  the right table/subset expressible (class 2), not to describe the wrong one.
- One class, one fix per case. If two gaps stack, fix the upstream one first
  (usually table/grain before subset) and let the re-eval surface the rest.
- If the tell is genuinely ambiguous (you cannot tell which column a term maps
  to), the fix type is `description` and the `diagnosis` states the ambiguity as
  a question for a human — never invent the mapping.

## Phase 4 — Propose grounded fixes

Emit one typed diff per gap, each of this shape:

```
{ case_id, gap_class,               // the # from the map, named
  diagnosis,                        // one sentence: what was missing, from SQL vs model
  type,                             // filter | relationship | description | glossary_term | popular_query | model-only
  target_table, name,
  expr, columns_used[],             // MUST be verbatim from the model structure
  description }                     // when-to-use text a downstream consumer will read
```

Hard grounding check before you output: for every `expr`/`columns_used`, confirm
the token appears in the Phase-1 model structure. Drop (don't fudge) any fix you
can't ground, and note it as an ungrounded gap for a human.

## Phase 5 — Hand off

- To the **fix** step: apply the diffs to the model and redeploy (patch the model
  for the in-session result; do not wait on a rebuild-from-Atlan — gold-sync lag
  and governance approval are off the critical path here). Then re-eval the
  affected cases only, against the SAME fresh goldens, and report before→after.
- To the **`update-to-atlan`** skill (the loop's close for *persistable* fixes):
  for each grounded fix whose type is a write-back type (`description` /
  `glossary_term` / `filter` / `relationship` / `popular_query`), hand it to
  `update-to-atlan`, which presents the exact diff + target and performs the write.
  - **The write is gated on the human's approval.** If the user's prompt authorized
    persisting ("write the fix back to Atlan"), proceed. Otherwise present the fix
    (via `update-to-atlan`, or plainly if non-interactive) and **stop for approval**
    — do NOT treat a bypass/non-interactive permission mode as standing approval for
    a write to production Atlan. Reaching the gate is the goal; crossing it needs a human.
  - **model-only fixes** (a metric's calculation, a verified query, a time
    dimension with no governed Atlan window) are applied to the model and reported —
    there is nothing to dispatch to `update-to-atlan`.
  - Do NOT write the entity inline with ad-hoc MCP/Bash — the `update-to-atlan` skill owns the write.
- Loop: if the target Y% isn't met and iterations remain, feed the new failures
  back to Phase 2. Stop at Y% or the iteration budget, and report which gaps were
  filled (and from which source) and which remain.

## Style rules

- State the gap class for every failure — the value of this skill is the legible
  map, not just the patch. A silent fix teaches the field team nothing.
- Never read goldens; never invent names; never teach to the test. If any of the
  three is at risk, STOP and surface it rather than produce a fix that looks good
  on the eval and fails in production.
- Report honestly: "1 of 5 fixed, 3 need a human" beats a fabricated clean climb.
- Never log secrets or credential values.

## Before you end this skill — presentation gate (read this last)

Do not end by silently dropping a grounded fix. Before your closing summary, for
each grounded, persistable fix, **present it** — surface the exact typed diff +
its Atlan target (dispatching `update-to-atlan` is the cleanest way to present, since
it shows the diff and holds at its approval gate). Then:

1. If the user authorized persisting, let the write proceed and report the
   read-back (`status` / `verbatim_ok`).
2. If not (or the run is non-interactive), present the fix and **stop for the
   human's approval** — do NOT write to production Atlan on your own authority.
3. Apply **model-only** fixes to the model and report them; there is nothing to persist.

A fix you found but neither presented nor applied is the failure mode to avoid —
name every gap and its fix. If there is genuinely no grounded fix, say so.

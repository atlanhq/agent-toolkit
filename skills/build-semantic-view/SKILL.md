---
name: build-semantic-view
description: Build a semantic model (Snowflake Cortex Analyst, Databricks metric view, Databricks Genie, dbt MetricFlow, or Atlan's own canonical form) for a confirmed set of Atlan tables. Columns, datatypes and descriptions come from the Atlan catalog; which columns are labels, dates or numbers is decided by rules grounded in catalog facts, with no AI authoring. Atlan builds the file and returns it - nothing is created or stored in the tenant. Use after the user has confirmed which tables to model. Requires an Atlan API key.
---

# Build a semantic view

Take a **confirmed set of Atlan tables** and produce a semantic model file for the tool that
will answer questions over them.

A semantic model tells a querying tool what the tables mean: which columns are labels you filter
by, which are dates you group by, which are numbers you can add up, how the tables join, and
what the business calls each thing. Snowflake Cortex Analyst, Databricks metric views,
Databricks Genie and dbt each want that same information in their own file format.

## What this produces, and what it does not do

Atlan builds the model and hands it back. **Nothing is created in the tenant** - no stored
object, no saved file, no identifier to track. The file is the deliverable, and deploying it is
not this skill's job.

Everything in the model traces to something already in the catalog:

| what | where it comes from |
|---|---|
| column names, datatypes, descriptions | the Atlan catalog's own column records |
| label / date / number for each column | rules over catalog facts: semantics the customer declared in dbt, how columns are used in observed queries, key flags, real date types, profiling statistics, sampled values |
| joins between tables | joins Atlan has observed in real queries |
| known-good example queries | analyst queries Atlan has already seen |
| the model's business names | the display names and descriptions already on the assets |

Nothing is invented by a model. Where the catalog has no answer, the section comes back empty
and the gaps are reported rather than filled with a guess.

## Before you start

The user must have **confirmed which tables to model**. Do not choose tables for them: a
semantic model over the wrong tables produces confident wrong answers, which is worse than no
model. Use the search tools to help them decide, then build from what they confirm.

An **Atlan API key** is required. This skill calls an Atlan HTTP endpoint directly, and that
endpoint authenticates with a key rather than the browser sign-in the rest of this plugin uses.
The user creates one in Atlan under Settings, then API tokens.

```bash
export ATLAN_BASE_URL=https://<your-tenant>.atlan.com
export ATLAN_API_KEY=<the key>
```

`ATLAN_WISDOM_URL` is an optional third variable that points the script at an Atlan service
directly instead of at the tenant gateway. Leave it unset for normal use. It exists so this path
can be exercised against a service before release, and setting it wrongly will make every call
fail with a connection error rather than anything more helpful.

## Build it

**Run this as a single blocking call in the foreground, and wait for it.** Allow at least 20
minutes. Do not background it, detach it, or start it and poll for the file later.

This matters more than it sounds. The build is one long request that holds the connection open for
minutes, so if the process is detached and the parent moves on, the request dies with **no output
file and no error message anywhere** - it simply looks as though nothing happened. That is exactly
what happened the first time this skill was followed: the build was backgrounded on the strength of
"it takes minutes", the process was lost, and the failure was silent.

```bash
python skills/build-semantic-view/build_semantic_model.py \
  --tables default/snowflake/1700000000/DB/SCHEMA/ORDERS \
           default/snowflake/1700000000/DB/SCHEMA/CUSTOMERS \
  --engine cortex \
  --out orders.yaml
```

### Which engine to ask for

| engine | what you get |
|---|---|
| `cortex` | a Snowflake Cortex Analyst semantic model. `snowflake` means the same thing |
| `databricks` | a Databricks Unity Catalog metric view, ready for a deploy to read |
| `genie` | a Databricks Genie space configuration |
| `dbt` | dbt MetricFlow semantic models |
| `atlan` | Atlan's own form of the model, which every other one is produced from. Ask for this when you want the meaning without committing to a vendor |

The engine names a **result**, not a step. Asking for `databricks` gives you the file a deploy
reads, not an intermediate.

## Reading the result

The script prints what it built and writes the file. Four things are worth checking before
anyone relies on the output:

- **Did every table make it?** A table that could not be modelled is named, and the script
  exits non-zero. The file still contains the tables that worked, so a single bad table does
  not cost you the rest. A model quietly missing a table is the failure worth catching here -
  the gap otherwise turns up later, in wrong answers.
- **Are there numbers to add up?** A model whose columns are all labels cannot aggregate
  anything. If the catalog has no declared semantics, no observed query usage, no key flags and
  no profiling for these tables, that is what you will get, and the honest fix is better catalog
  coverage rather than a different build.
- **Are there joins?** Joins come from queries Atlan has observed. A tenant with no observed
  joins on these tables produces a model with none, and questions that need a join will not be
  answerable.
- **What was left out?** The script prints a count of items the build could not ground in the
  catalog, and the reasons come back in the reply rather than inside the file. Do not go looking
  for a list of them in the YAML: only Atlan's own form (`--engine atlan`) carries one, as a
  `dropped_metrics` section. The vendor formats do not, and a count of zero is common and fine.
  Entries dropped because they refer to tables outside this model are expected and can be ignored.

**Did the target engine accept it?** That is a separate question from whether the model is well
formed, and the reply answers it in a `validation` field. For Snowflake there is a documented dry run,
`SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML(..., TRUE)`, which validates without creating anything, and
Atlan attempts it during the build. Read the status rather than assuming:

| `validation.status` | what it means |
|---|---|
| `valid` | Snowflake compiled the model. Tables, identifiers and expressions all resolved |
| `invalid` | Snowflake **rejected** it, and `error` carries what it said. The build reports failure and still returns the file so you can see what was wrong |
| `unverified` | the connection's role lacks the privilege to run the compile. `error` names the grant needed. Not a defect in the model |
| `skipped` | the check could not run at all, for example the verify service was unreachable. Not a defect in the model |
| `not_available` | this engine offers no such check. True of every format except Snowflake Cortex |

The states other than `valid` and `invalid` are deliberately not failures, so **a successful build does
not on its own mean the file was checked.** For anything other than `valid`, run the dry run yourself
or deploy somewhere disposable first, before trusting the file in anything that matters.

## Time and cost

A build reads the catalog for every table, so expect **minutes, not seconds** - roughly a
minute per table. It is one request that holds the connection; that is normal, not a hang. No
queries are run against the customer's warehouse, and no AI model authors any part of the
output.

## Errors you may see

- **Rejected key** - the key does not belong to the tenant in `ATLAN_BASE_URL`, or has expired.
- **Tables not found** - Atlan answers the same way for a table that does not exist and one the
  key cannot see, so the message names the ones it could not find. Check the qualified names
  first, then whether the key's persona can read those assets.
- **An engine name it does not know** - the request is refused rather than falling back to a
  different format, because a plausible-looking file for the wrong engine only surfaces the
  mistake at deploy time.

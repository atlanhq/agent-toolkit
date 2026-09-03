---
name: update-to-atlan
description: Persist a context fix back to Atlan so every future semantic-model build and every other consumer reuses it - a join, a named filter, a business question with its SQL, an asset description, or a glossary term. Use when someone asks to write a fix back to Atlan, persist context, push a join or filter to Atlan, or save a definition.
---

# Write a context fix back to Atlan

A fix found while reading a model is worth making once. Writing it back is what makes the
next build, and every other consumer, inherit it.

## Which tool

| The fix | Tool |
|---|---|
| a join between two tables | `create_sql_insight` with `kind="join"` |
| a named filter on a column | `create_sql_insight` with `kind="filter"` |
| a business question and the SQL that answers it | `create_sql_insight` with `kind="question"` |
| an asset's description | `update_assets_tool` |
| a business term | `create_glossary_terms` |

A metric is not a write type of its own. Persist what it means as a glossary term; its
calculation belongs in the semantic model.

## The approval gate

`create_sql_insight` defaults to `mode="propose"`. Call it that way first, show the user
the preview, and wait for them to say yes before calling again with `mode="execute"`.

**The permission prompt your client shows for running a tool is not that approval.** It
asks whether you may call the tool; it does not ask whether this content should be written
to the company's catalog. Ask separately, in words.

The preview reports an `action`. Say which one it is:

- **create** - nothing with this identity exists yet.
- **update** - this identity already exists and the write will land on it. Atlan derives
  the identity from the content, so this converges with what is already there rather than
  making a duplicate, but it is still an edit to an existing row.
- **revive** - it exists but was archived, and writing will bring it back.

## After the write

The result carries `guid`, `qualified_name`, `status` and `verbatim_ok`. Report what
landed. If `verbatim_ok` is false, what came back is not what was sent: say so rather than
reporting success.

To undo one, use `manage_asset_lifecycle_tool` with `PURGE` on the guid. An archive alone
leaves the row resolvable.

Write one fix per call. If several were found, take them one at a time so each gets its own
approval.

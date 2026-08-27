# Glossary — terms, categories, glossaries

Three types, one hierarchy: `AtlasGlossary` → `AtlasGlossaryCategory`
(nestable) → `AtlasGlossaryTerm`. Terms hang off leaf categories, not parents.

## Finding terms

Meaning-based ask ("what do we call monthly active users?") →
`semantic_search`, verbatim.

Exact / scoped ask → `search_assets`:

```json
{"asset_type": "AtlasGlossaryTerm",
 "glossary_qualified_name": "<glossary QN>",
 "conditions": {"name": {"operator": "contains", "value": "revenue"}}}
```

`glossary_qualified_name` is the correct way to scope to one glossary. Do not
try to pattern-match `qualifiedName` — for glossary objects it is an opaque
`{nanoId}@{glossaryQN}` string, so `contains` / `startswith` on it will not do
what you expect.

## Walking the category tree

Ask for `parentCategory` and `qualifiedName` in `attributes` when traversing —
without them you cannot tell a root category from a nested one. A root
category has no parent.

"Terms in category X" means terms in X **and everything beneath it**:

1. Start from X's GUID.
2. Find its child categories, then their children, until none remain.
3. Collect terms across every category GUID including X.

Stopping at step 1 silently under-reports whenever the taxonomy nests, which
is the common case.

## Assets linked to a term

`search_assets` with `assigned_term_guids=["<term guid>"]`. Not a `conditions`
entry — `meanings` is a relationship attribute and is not searchable there.

The reverse ("which terms are on this asset") comes from `get_assets` with the
`meanings` relationship, not from a search.

## Coverage questions

"How many terms have no linked assets?" / "which terms are unused?" —
`search_assets` with `asset_type="AtlasGlossaryTerm"`,
`glossary_qualified_name` set, and an aggregation on `__meanings`. That
combination is recognised and returns linked/unlinked counts directly; other
parameters passed alongside it are ignored, so send only those three.

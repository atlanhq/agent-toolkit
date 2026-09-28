# Domains and data products

- **DataDomain** — a business area ("Sales", "Finance"). May contain
  subdomains (nestable, any depth), data products, and assets linked directly.
- **DataProduct** — a curated set of assets inside a domain or subdomain.
- **Output ports** — the product's assets exposed for consumption.
- **Input ports** — derived: assets overlapping another product's output ports.

Products can sit directly under a domain; subdomains are optional. Assets can
belong to a domain without belonging to any product.

## Finding them

Both are ordinary asset types, so `search_assets` with
`asset_type="DataDomain"` or `"DataProduct"` lists them, and
`semantic_search("finance domain")` finds them by meaning.

## Lifecycle — filter it

A product's status is Draft → Active → Sunset. Only **Active** is
production-ready. Default to Active unless the user asks about drafts or
sunset products, and say which you filtered to.

## "All assets in domain X" is multi-step

A domain's assets are not just the ones tagged with its GUID. Getting this
right:

1. Resolve the root domain's GUID.
2. Find **all** subdomains, recursively, until no children remain. Collect
   every domain GUID.
3. Find **all** products under every collected domain.
4. Search assets across all domain GUIDs and all product GUIDs — pass the
   domain GUIDs in `domain_guids`.

Skipping 2 and 3 is the standard failure: it returns the assets pinned to the
top-level domain and silently drops everything under subdomains and products.

Shortcut for discovering the hierarchy: subdomains and products share the
parent domain's `qualifiedName` as a prefix, so a `startswith` condition on
`qualifiedName` against the domain's QN surfaces the whole subtree in one call.
Verify the result against the recursive walk before reporting a count.

## Attributes worth asking for

On products: status, criticality, sensitivity, visibility, output and input
ports. On domains: parent domain, subdomains, stakeholders, products. Use
`describe_asset_type("DataProduct")` when you need the exact camelCase field
names.

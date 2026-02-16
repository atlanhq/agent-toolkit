---
name: update-assets
description: Update data asset properties in Atlan including descriptions, certificates, README, glossary terms, and custom metadata. Use when users want to document, certify, or enrich their data assets.
---

# Update Data Assets

The user wants to update properties of data assets in Atlan.

## Instructions

- Parse the user's intent from: `$ARGUMENTS`
- Use `update_assets_tool` to modify asset properties

### Updatable Attributes

1. **user_description** - Set or update the asset's description
2. **certificate_status** - Set certification: VERIFIED, DRAFT, or DEPRECATED
3. **readme** - Set a detailed README in Markdown format
4. **term** - Manage glossary term associations:
   - `append`: Add terms to existing associations
   - `replace`: Replace all term associations
   - `remove`: Remove specific term associations
5. **custom_metadata** - Set or update custom metadata values:
   - Always use `discover_custom_metadata_tool` first to find exact set and attribute names
   - Can set attributes, remove specific attributes, or remove entire sets

## Workflow

1. Search for the target asset to get guid, name, type_name, qualified_name
2. For custom metadata: discover exact field names first
3. For terms: search for glossary terms to get their GUIDs
4. Execute the update
5. Confirm what was updated

## Batch Updates
Multiple assets can be updated in a single call by passing a list of assets with corresponding attribute values.

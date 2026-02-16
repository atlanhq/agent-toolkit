---
name: manage-glossary
description: Create and manage business glossaries, terms, and categories in Atlan. Use when users want to define business terminology, create glossaries, add terms, or organize categories.
---

# Manage Business Glossary

The user wants to work with Atlan's business glossary. This includes creating glossaries, terms, and categories.

## Instructions

- Parse the user's intent from: `$ARGUMENTS`
- **Before creating anything**, search first to check for existing glossaries/terms/categories to avoid duplicates
- Use `semantic_search_tool` with the glossary/term name to check existence

### Creating Glossaries
- Use `create_glossaries` with name, description, and optional certificate status
- Certificate statuses: VERIFIED, DRAFT, DEPRECATED

### Creating Terms
- Use `create_glossary_terms` - requires `glossary_guid` (search for the glossary first)
- Terms can optionally be assigned to categories via `category_guids`
- Two terms with the same name CANNOT exist within the same glossary

### Creating Categories
- Use `create_glossary_categories` - requires `glossary_guid`
- Categories can be nested using `parent_category_guid`
- Two categories with the same name CANNOT exist at the same level within a glossary

## Workflow

1. Search for existing glossary/terms/categories
2. If glossary doesn't exist, create it first
3. Create categories if needed
4. Create terms and link to glossary and categories
5. Confirm what was created with GUIDs and qualified names

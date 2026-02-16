---
name: review-governance
description: Review and improve data governance posture for assets. Checks descriptions, certifications, glossary terms, owners, and data quality rules. Use when users want a governance audit or want to improve asset documentation.
---

# Data Governance Review

Perform a governance review of data assets in Atlan. This checks for documentation completeness, certification status, term associations, and data quality coverage.

## Instructions

- Parse the user's intent from: `$ARGUMENTS`

## Review Checklist

For each asset, check:

1. **Description**: Does the asset have a meaningful `user_description`?
2. **Certificate**: Is it certified (VERIFIED, DRAFT, or DEPRECATED)?
3. **Owner**: Does it have assigned owners?
4. **Glossary Terms**: Are relevant business terms linked?
5. **README**: Does it have detailed documentation?
6. **Custom Metadata**: Are governance-related metadata fields populated?
7. **Lineage**: Is lineage available?
8. **Data Quality**: Are there DQ rules configured?

## Workflow

1. Search for the asset(s) using `semantic_search_tool` with `include_custom_metadata=true`
2. For each asset, evaluate the checklist above
3. Present a governance scorecard showing what's complete and what's missing
4. Suggest specific improvements (e.g., "Add a description", "Create a DQ rule for null checks")
5. Optionally help the user fix gaps by updating assets or creating rules

## Output Format

Present results as a governance report:
- Asset name and type
- Governance score (e.g., 5/8 checks passing)
- Passing checks with green indicators
- Failing checks with specific recommendations
- Priority actions to improve governance posture

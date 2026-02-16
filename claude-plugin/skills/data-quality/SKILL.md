---
name: data-quality
description: Create, update, schedule, and manage data quality rules in Atlan. Use when users want to set up data quality checks, monitor data health, or enforce data standards.
---

# Manage Data Quality Rules

The user wants to work with data quality rules in Atlan.

## Instructions

- Parse the user's intent from: `$ARGUMENTS`

### Creating Rules
Use `create_dq_rules_tool`. Supported rule types:
- **Completeness**: Null Count, Null Percentage, Blank Count, Blank Percentage
- **Statistical**: Min Value, Max Value, Average, Standard Deviation
- **Uniqueness**: Unique Count, Duplicate Count
- **Validity**: Regex, String Length, Valid Values
- **Timeliness**: Freshness (requires threshold_unit: DAYS/HOURS/MINUTES)
- **Volume**: Row Count (table-level, no column needed)
- **Custom**: Custom SQL (requires custom_sql, rule_name, dimension)

Required fields: `rule_type`, `asset_qualified_name`, `threshold_value`
Column-level rules also require: `column_qualified_name`

### Updating Rules
Use `update_dq_rules_tool` with the rule's `qualified_name`.

### Scheduling Rules
Use `schedule_dq_rules_tool` with cron expression and timezone.

### Deleting Rules
Use `delete_dq_rules_tool` with rule GUID(s).

## Workflow

1. Search for the target asset to get its qualified_name (and column qualified_name if needed)
2. Create appropriate DQ rules based on the user's requirements
3. Optionally schedule rule execution
4. Confirm what was created

## Alert Priorities
- LOW, NORMAL (default), URGENT

## Threshold Operators
- EQUAL, GREATER_THAN, GREATER_THAN_EQUAL, LESS_THAN, LESS_THAN_EQUAL, BETWEEN

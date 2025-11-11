"""
Data Quality Rules creation tool for Atlan MCP server.

This module provides functionality to create data quality rules in Atlan,
supporting column-level, table-level, and custom SQL rules.
"""

from __future__ import annotations
import logging
from typing import Dict, Any, List, Union

from pyatlan.model.assets import DataQualityRule, Table, Column
from pyatlan.model.enums import (
    DataQualityRuleAlertPriority,
    DataQualityRuleThresholdCompareOperator,
    DataQualityDimension,
    DataQualityRuleThresholdUnit,
    DataQualityRuleTemplateConfigRuleConditions,
)
from pyatlan.model.dq_rule_conditions import DQRuleConditionsBuilder

from client import get_atlan_client
from .models import (
    DQRuleSpecification,
    DQRuleType,
    DQAlertPriority,
    DQThresholdCompareOperator,
    DQDimension,
    DQThresholdUnit,
    DQRuleConditionType,
)

logger = logging.getLogger(__name__)


# Mapping dictionaries to convert our enums to PyAtlan enums
ALERT_PRIORITY_MAP = {
    DQAlertPriority.LOW: DataQualityRuleAlertPriority.LOW,
    DQAlertPriority.NORMAL: DataQualityRuleAlertPriority.NORMAL,
    DQAlertPriority.URGENT: DataQualityRuleAlertPriority.URGENT,
}

THRESHOLD_OPERATOR_MAP = {
    DQThresholdCompareOperator.EQUAL: DataQualityRuleThresholdCompareOperator.EQUAL,
    DQThresholdCompareOperator.GREATER_THAN: DataQualityRuleThresholdCompareOperator.GREATER_THAN,
    DQThresholdCompareOperator.GREATER_THAN_EQUAL: DataQualityRuleThresholdCompareOperator.GREATER_THAN_EQUAL,
    DQThresholdCompareOperator.LESS_THAN: DataQualityRuleThresholdCompareOperator.LESS_THAN,
    DQThresholdCompareOperator.LESS_THAN_EQUAL: DataQualityRuleThresholdCompareOperator.LESS_THAN_EQUAL,
    DQThresholdCompareOperator.BETWEEN: DataQualityRuleThresholdCompareOperator.BETWEEN,
}

DIMENSION_MAP = {
    DQDimension.COMPLETENESS: DataQualityDimension.COMPLETENESS,
    DQDimension.VALIDITY: DataQualityDimension.VALIDITY,
    DQDimension.UNIQUENESS: DataQualityDimension.UNIQUENESS,
    DQDimension.TIMELINESS: DataQualityDimension.TIMELINESS,
    DQDimension.VOLUME: DataQualityDimension.VOLUME,
    DQDimension.ACCURACY: DataQualityDimension.ACCURACY,
    DQDimension.CONSISTENCY: DataQualityDimension.CONSISTENCY,
}

THRESHOLD_UNIT_MAP = {
    DQThresholdUnit.DAYS: DataQualityRuleThresholdUnit.DAYS,
    DQThresholdUnit.HOURS: DataQualityRuleThresholdUnit.HOURS,
    DQThresholdUnit.MINUTES: DataQualityRuleThresholdUnit.MINUTES,
}

CONDITION_TYPE_MAP = {
    DQRuleConditionType.STRING_LENGTH_EQUALS: DataQualityRuleTemplateConfigRuleConditions.STRING_LENGTH_EQUALS,
    DQRuleConditionType.STRING_LENGTH_BETWEEN: DataQualityRuleTemplateConfigRuleConditions.STRING_LENGTH_BETWEEN,
    DQRuleConditionType.STRING_LENGTH_GREATER_THAN: DataQualityRuleTemplateConfigRuleConditions.STRING_LENGTH_GREATER_THAN,
    DQRuleConditionType.STRING_LENGTH_GREATER_THAN_EQUALS: DataQualityRuleTemplateConfigRuleConditions.STRING_LENGTH_GREATER_THAN_EQUALS,
    DQRuleConditionType.STRING_LENGTH_LESS_THAN: DataQualityRuleTemplateConfigRuleConditions.STRING_LENGTH_LESS_THAN,
    DQRuleConditionType.STRING_LENGTH_LESS_THAN_EQUALS: DataQualityRuleTemplateConfigRuleConditions.STRING_LENGTH_LESS_THAN_EQUALS,
    DQRuleConditionType.REGEX_MATCH: DataQualityRuleTemplateConfigRuleConditions.REGEX_MATCH,
    DQRuleConditionType.REGEX_NOT_MATCH: DataQualityRuleTemplateConfigRuleConditions.REGEX_NOT_MATCH,
    DQRuleConditionType.IN_LIST: DataQualityRuleTemplateConfigRuleConditions.IN_LIST,
    DQRuleConditionType.NOT_IN_LIST: DataQualityRuleTemplateConfigRuleConditions.NOT_IN_LIST,
}

# Rule types that require column_qualified_name
COLUMN_LEVEL_RULES = {
    DQRuleType.NULL_COUNT,
    DQRuleType.NULL_PERCENTAGE,
    DQRuleType.BLANK_COUNT,
    DQRuleType.BLANK_PERCENTAGE,
    DQRuleType.MIN_VALUE,
    DQRuleType.MAX_VALUE,
    DQRuleType.AVERAGE,
    DQRuleType.STANDARD_DEVIATION,
    DQRuleType.UNIQUE_COUNT,
    DQRuleType.DUPLICATE_COUNT,
    DQRuleType.REGEX,
    DQRuleType.STRING_LENGTH,
    DQRuleType.VALID_VALUES,
    DQRuleType.FRESHNESS,
}

# Rule types that work at table level
TABLE_LEVEL_RULES = {
    DQRuleType.ROW_COUNT,
}

# Rule types that support conditions
CONDITIONAL_RULES = {
    DQRuleType.STRING_LENGTH,
    DQRuleType.REGEX,
    DQRuleType.VALID_VALUES,
}


def create_dq_rules(
    rules: Union[Dict[str, Any], List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Create one or multiple data quality rules in Atlan.
    
    Args:
        rules (Union[Dict[str, Any], List[Dict[str, Any]]]): Either a single rule
            specification or a list of rule specifications.
    
    Returns:
        Dict[str, Any]: Dictionary containing:
            - created_count: Number of rules successfully created
            - created_rules: List of created rule details (guid, qualified_name, rule_type)
            - errors: List of any errors encountered
    
    Raises:
        Exception: If there's an error creating the rules.
    """
    # Convert single rule to list for consistent handling
    data = rules if isinstance(rules, list) else [rules]
    logger.info(f"Creating {len(data)} data quality rule(s)")
    logger.debug(f"Rule specifications: {data}")
    
    result = {
        "created_count": 0,
        "created_rules": [],
        "errors": []
    }
    
    try:
        # Validate and parse specifications
        specs = []
        for idx, item in enumerate(data):
            try:
                spec = DQRuleSpecification(**item)
                validation_errors = _validate_rule_specification(spec)
                if validation_errors:
                    for error in validation_errors:
                        result["errors"].append(f"Rule {idx + 1}: {error}")
                    continue
                specs.append(spec)
            except Exception as e:
                result["errors"].append(f"Rule {idx + 1} validation error: {str(e)}")
                logger.error(f"Error parsing rule specification {idx + 1}: {e}")
        
        if not specs:
            logger.warning("No valid rule specifications to create")
            return result
        
        # Get Atlan client
        client = get_atlan_client()
        
        # Create rules
        created_assets = []
        for spec in specs:
            try:
                logger.debug(f"Creating {spec.rule_type.value} rule for {spec.asset_qualified_name}")
                
                # Route to appropriate creator based on rule type
                if spec.rule_type == DQRuleType.CUSTOM_SQL:
                    rule = _create_custom_sql_rule(spec, client)
                elif spec.rule_type in TABLE_LEVEL_RULES:
                    rule = _create_table_level_rule(spec, client)
                elif spec.rule_type in COLUMN_LEVEL_RULES:
                    rule = _create_column_level_rule(spec, client)
                else:
                    result["errors"].append(f"Unsupported rule type: {spec.rule_type.value}")
                    continue
                
                created_assets.append(rule)
                
            except Exception as e:
                error_msg = f"Error creating {spec.rule_type.value} rule: {str(e)}"
                result["errors"].append(error_msg)
                logger.error(error_msg)
                logger.exception("Exception details:")
        
        # Bulk save all created rules
        if created_assets:
            logger.info(f"Saving {len(created_assets)} data quality rules")
            response = client.asset.save(created_assets)
            
            # Process response
            for created_rule in response.mutated_entities.CREATE:
                result["created_rules"].append({
                    "guid": created_rule.guid,
                    "qualified_name": created_rule.qualified_name,
                    "rule_type": created_rule.dq_rule_type if hasattr(created_rule, 'dq_rule_type') else None,
                })
            
            result["created_count"] = len(result["created_rules"])
            logger.info(f"Successfully created {result['created_count']} data quality rules")
        
        return result
        
    except Exception as e:
        error_msg = f"Error in bulk rule creation: {str(e)}"
        logger.error(error_msg)
        logger.exception("Exception details:")
        result["errors"].append(error_msg)
        return result


def _validate_rule_specification(spec: DQRuleSpecification) -> List[str]:
    """
    Validate a rule specification based on rule type requirements.
    
    Args:
        spec (DQRuleSpecification): The rule specification to validate
    
    Returns:
        List[str]: List of validation error messages (empty if valid)
    """
    errors = []
    
    # Column-level rules require column_qualified_name
    if spec.rule_type in COLUMN_LEVEL_RULES and not spec.column_qualified_name:
        errors.append(f"{spec.rule_type.value} requires column_qualified_name")
    
    # Custom SQL rules require specific fields
    if spec.rule_type == DQRuleType.CUSTOM_SQL:
        if not spec.custom_sql:
            errors.append("Custom SQL rules require custom_sql field")
        if not spec.rule_name:
            errors.append("Custom SQL rules require rule_name field")
        if not spec.dimension:
            errors.append("Custom SQL rules require dimension field")
    
    # Conditional rules should have conditions
    if spec.rule_type in CONDITIONAL_RULES and not spec.rule_conditions:
        logger.warning(f"{spec.rule_type.value} rule created without conditions")
    
    # Freshness rules require threshold_unit
    if spec.rule_type == DQRuleType.FRESHNESS and not spec.threshold_unit:
        errors.append("Freshness rules require threshold_unit (DAYS, HOURS, or MINUTES)")
    
    # All rules require threshold_value
    if spec.threshold_value is None:
        errors.append(f"{spec.rule_type.value} requires threshold_value")
    
    return errors


def _create_column_level_rule(
    spec: DQRuleSpecification,
    client
) -> DataQualityRule:
    """
    Create a column-level data quality rule.
    
    Args:
        spec (DQRuleSpecification): Rule specification
        client: Atlan client instance
    
    Returns:
        DataQualityRule: Created rule asset
    """
    logger.debug(f"Creating column-level rule: {spec.rule_type.value}")
    
    # Prepare parameters
    params = {
        "client": client,
        "rule_type": spec.rule_type.value,
        "asset": Table.ref_by_qualified_name(qualified_name=spec.asset_qualified_name),
        "column": Column.ref_by_qualified_name(qualified_name=spec.column_qualified_name),
        "threshold_value": spec.threshold_value,
        "alert_priority": ALERT_PRIORITY_MAP[spec.alert_priority],
    }
    
    # Add optional parameters
    if spec.threshold_compare_operator:
        params["threshold_compare_operator"] = THRESHOLD_OPERATOR_MAP[spec.threshold_compare_operator]
    
    if spec.threshold_unit:
        params["threshold_unit"] = THRESHOLD_UNIT_MAP[spec.threshold_unit]
    
    if spec.row_scope_filtering_enabled:
        params["row_scope_filtering_enabled"] = spec.row_scope_filtering_enabled
    
    # Handle rule conditions for conditional rules
    if spec.rule_conditions and spec.rule_type in CONDITIONAL_RULES:
        rule_conditions = _build_rule_conditions(spec.rule_conditions)
        params["rule_conditions"] = rule_conditions
    
    # Create the rule
    dq_rule = DataQualityRule.column_level_rule_creator(**params)
    
    # Add description if provided
    if spec.description:
        dq_rule.description = spec.description
    
    return dq_rule


def _create_table_level_rule(
    spec: DQRuleSpecification,
    client
) -> DataQualityRule:
    """
    Create a table-level data quality rule.
    
    Args:
        spec (DQRuleSpecification): Rule specification
        client: Atlan client instance
    
    Returns:
        DataQualityRule: Created rule asset
    """
    logger.debug(f"Creating table-level rule: {spec.rule_type.value}")
    
    # Prepare parameters
    params = {
        "client": client,
        "rule_type": spec.rule_type.value,
        "asset": Table.ref_by_qualified_name(qualified_name=spec.asset_qualified_name),
        "threshold_value": spec.threshold_value,
        "alert_priority": ALERT_PRIORITY_MAP[spec.alert_priority],
    }
    
    # Add optional parameters
    if spec.threshold_compare_operator:
        params["threshold_compare_operator"] = THRESHOLD_OPERATOR_MAP[spec.threshold_compare_operator]
    
    # Create the rule
    dq_rule = DataQualityRule.table_level_rule_creator(**params)
    
    # Add description if provided
    if spec.description:
        dq_rule.description = spec.description
    
    return dq_rule


def _create_custom_sql_rule(
    spec: DQRuleSpecification,
    client
) -> DataQualityRule:
    """
    Create a custom SQL data quality rule.
    
    Args:
        spec (DQRuleSpecification): Rule specification
        client: Atlan client instance
    
    Returns:
        DataQualityRule: Created rule asset
    """
    logger.debug(f"Creating custom SQL rule: {spec.rule_name}")
    
    # Prepare parameters
    params = {
        "client": client,
        "rule_name": spec.rule_name,
        "asset": Table.ref_by_qualified_name(qualified_name=spec.asset_qualified_name),
        "custom_sql": spec.custom_sql,
        "threshold_value": spec.threshold_value,
        "alert_priority": ALERT_PRIORITY_MAP[spec.alert_priority],
        "dimension": DIMENSION_MAP[spec.dimension],
    }
    
    # Add optional parameters
    if spec.threshold_compare_operator:
        params["threshold_compare_operator"] = THRESHOLD_OPERATOR_MAP[spec.threshold_compare_operator]
    
    if spec.description:
        params["description"] = spec.description
    
    # Create the rule
    dq_rule = DataQualityRule.custom_sql_creator(**params)
    
    return dq_rule


def _build_rule_conditions(conditions: List) -> Any:
    """
    Build DQRuleConditionsBuilder from condition specifications.
    
    Args:
        conditions (List): List of DQRuleCondition objects or dicts
    
    Returns:
        Built rule conditions object
    """
    logger.debug(f"Building rule conditions for {len(conditions)} condition(s)")
    
    builder = DQRuleConditionsBuilder()
    
    for condition in conditions:
        # Handle both dict and object formats
        if isinstance(condition, dict):
            condition_type = CONDITION_TYPE_MAP[DQRuleConditionType(condition["type"])]
            value = condition.get("value")
            min_value = condition.get("min_value")
            max_value = condition.get("max_value")
        else:
            condition_type = CONDITION_TYPE_MAP[condition.type]
            value = condition.value
            min_value = condition.min_value
            max_value = condition.max_value
        
        # Build condition based on type
        condition_params = {"type": condition_type}
        
        if value is not None:
            condition_params["value"] = value
        
        if min_value is not None:
            condition_params["min_value"] = min_value
        
        if max_value is not None:
            condition_params["max_value"] = max_value
        
        builder.add_condition(**condition_params)
    
    return builder.build()
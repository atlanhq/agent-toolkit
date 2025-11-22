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
from .models import DQRuleSpecification, DQRuleType

logger = logging.getLogger(__name__)


def create_dq_rules(
    rules: Union[Dict[str, Any], List[Dict[str, Any]]],
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

    result = {"created_count": 0, "created_rules": [], "errors": []}

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
                logger.debug(
                    f"Creating {spec.rule_type.value} rule for {spec.asset_qualified_name}"
                )
                rule = _create_dq_rule(spec, client)
                created_assets.append(rule)

            except Exception as e:
                error_msg = f"Error creating {spec.rule_type.value} rule: {str(e)}"
                result["errors"].append(error_msg)
                logger.error(error_msg)

        # Bulk save all created rules
        if created_assets:
            logger.info(f"Saving {len(created_assets)} data quality rules")
            response = client.asset.save(created_assets)

            # Process response
            for created_rule in response.mutated_entities.CREATE:
                result["created_rules"].append(
                    {
                        "guid": created_rule.guid,
                        "qualified_name": created_rule.qualified_name,
                        "rule_type": created_rule.dq_rule_type
                        if hasattr(created_rule, "dq_rule_type")
                        else None,
                    }
                )

            result["created_count"] = len(result["created_rules"])
            logger.info(
                f"Successfully created {result['created_count']} data quality rules"
            )

        return result

    except Exception as e:
        error_msg = f"Error in bulk rule creation: {str(e)}"
        logger.error(error_msg)
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
    config = spec.rule_type.get_rule_config()

    # Check if column is required but missing
    if config["requires_column"] and not spec.column_qualified_name:
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
    if config["supports_conditions"] and not spec.rule_conditions:
        logger.warning(f"{spec.rule_type.value} rule created without conditions")

    # Freshness rules require threshold_unit
    if spec.rule_type == DQRuleType.FRESHNESS and not spec.threshold_unit:
        errors.append(
            "Freshness rules require threshold_unit (DAYS, HOURS, or MINUTES)"
        )

    # All rules require threshold_value
    if spec.threshold_value is None:
        errors.append(f"{spec.rule_type.value} requires threshold_value")

    return errors


def _create_dq_rule(spec: DQRuleSpecification, client) -> DataQualityRule:
    """
    Create a data quality rule based on specification.

    This unified method handles all rule types by using the rule's configuration
    to determine the appropriate creator method and required parameters.

    Args:
        spec (DQRuleSpecification): Rule specification
        client: Atlan client instance

    Returns:
        DataQualityRule: Created rule asset
    """
    logger.debug(f"Creating {spec.rule_type.value} rule")

    # Get rule configuration
    config = spec.rule_type.get_rule_config()

    # Base parameters common to all rule types
    params = {
        "client": client,
        "asset": Table.ref_by_qualified_name(qualified_name=spec.asset_qualified_name),
        "threshold_value": spec.threshold_value,
        "alert_priority": DataQualityRuleAlertPriority[spec.alert_priority],
    }

    # Add rule-type specific parameters based on config
    if spec.rule_type == DQRuleType.CUSTOM_SQL:
        params.update(
            {
                "rule_name": spec.rule_name,
                "custom_sql": spec.custom_sql,
                "dimension": DataQualityDimension[spec.dimension],
            }
        )
    else:
        params["rule_type"] = spec.rule_type.value

        # Add column reference if required
        if config["requires_column"]:
            params["column"] = Column.ref_by_qualified_name(
                qualified_name=spec.column_qualified_name
            )

    # Add optional parameters
    if spec.threshold_compare_operator:
        params["threshold_compare_operator"] = DataQualityRuleThresholdCompareOperator[
            spec.threshold_compare_operator
        ]

    if spec.threshold_unit:
        params["threshold_unit"] = DataQualityRuleThresholdUnit[spec.threshold_unit]

    if spec.row_scope_filtering_enabled:
        params["row_scope_filtering_enabled"] = spec.row_scope_filtering_enabled

    # Add rule conditions if supported and provided
    if config["supports_conditions"] and spec.rule_conditions:
        params["rule_conditions"] = _build_rule_conditions(spec.rule_conditions)

    # Get the creator method from DataQualityRule and invoke it
    creator_method = getattr(DataQualityRule, config["creator_method"])
    dq_rule = creator_method(**params)

    # Add description if provided
    if spec.description:
        dq_rule.description = spec.description

    return dq_rule


def _build_rule_conditions(conditions: List[Dict[str, Any]]) -> Any:
    """
    Build DQRuleConditionsBuilder from condition specifications.

    Args:
        conditions (List[Dict[str, Any]]): List of condition dictionaries

    Returns:
        Built rule conditions object
    """
    logger.debug(f"Building rule conditions for {len(conditions)} condition(s)")

    builder = DQRuleConditionsBuilder()

    for condition in conditions:
        condition_type = DataQualityRuleTemplateConfigRuleConditions[condition["type"]]

        # Build condition parameters dynamically
        condition_params = {"type": condition_type}

        for key in ["value", "min_value", "max_value"]:
            if key in condition and condition[key] is not None:
                condition_params[key] = condition[key]

        builder.add_condition(**condition_params)

    return builder.build()

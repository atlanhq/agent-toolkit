"""
Data Quality Rules creation tool for Atlan MCP server.

This module provides functionality to create data quality rules in Atlan,
supporting column-level, table-level, and custom SQL rules.
"""

from __future__ import annotations
import logging
from typing import Dict, Any, List, Union

from pyatlan.model.assets import (
    DataQualityRule,
    Table,
    Column,
    View,
    MaterialisedView,
    SnowflakeDynamicTable,
)
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
    DQRuleCreationResponse,
    CreatedRuleInfo,
    DQRuleCondition,
    DQAssetType,
    DQRuleScheduleSpecification,
    DQRuleScheduleResponse,
    ScheduledAssetInfo,
    DQRuleDeleteSpecification,
    DQRuleDeleteResponse,
    DeletedRuleInfo,
)

logger = logging.getLogger(__name__)


def create_dq_rules(
    rules: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> DQRuleCreationResponse:
    """
    Create one or multiple data quality rules in Atlan.

    Args:
        rules (Union[Dict[str, Any], List[Dict[str, Any]]]): Either a single rule
            specification or a list of rule specifications.

    Returns:
        DQRuleCreationResponse: Response containing:
            - created_count: Number of rules successfully created
            - created_rules: List of created rule details (guid, qualified_name, rule_type)
            - errors: List of any errors encountered

    Raises:
        Exception: If there's an error creating the rules.
    """
    # Convert single rule to list for consistent handling
    data = rules if isinstance(rules, list) else [rules]
    logger.info(f"Creating {len(data)} data quality rule(s)")

    result = DQRuleCreationResponse()

    try:
        # Validate and parse specifications
        specs = []
        for idx, item in enumerate(data):
            try:
                # Pydantic model validation happens automatically
                spec = DQRuleSpecification(**item)
                specs.append(spec)
            except ValueError as e:
                # Pydantic validation errors
                result.errors.append(f"Rule {idx + 1} validation error: {str(e)}")
                logger.error(f"Error validating rule specification {idx + 1}: {e}")
            except Exception as e:
                result.errors.append(f"Rule {idx + 1} error: {str(e)}")
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
                rule = _create_dq_rule(spec, client)
                created_assets.append(rule)

            except Exception as e:
                error_msg = f"Error creating {spec.rule_type.value} rule: {str(e)}"
                result.errors.append(error_msg)
                logger.error(error_msg)

        if not created_assets:
            return result

        # Bulk save all created rules
        logger.info(f"Saving {len(created_assets)} data quality rules")
        response = client.asset.save(created_assets)

        # Process response
        for created_rule in response.mutated_entities.CREATE:
            result.created_rules.append(
                CreatedRuleInfo(
                    guid=created_rule.guid,
                    qualified_name=created_rule.qualified_name,
                    rule_type=created_rule.dq_rule_type
                    if hasattr(created_rule, "dq_rule_type")
                    else None,
                )
            )

        result.created_count = len(result.created_rules)
        logger.info(f"Successfully created {result.created_count} data quality rules")

        return result

    except Exception as e:
        error_msg = f"Error in bulk rule creation: {str(e)}"
        logger.error(error_msg)
        result.errors.append(error_msg)
        return result


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
    # Get rule configuration
    config = spec.rule_type.get_rule_config()

    # Determine asset class based on asset type
    if spec.asset_type == DQAssetType.VIEW:
        asset_class = View
    elif spec.asset_type == DQAssetType.MATERIALIZED_VIEW:
        asset_class = MaterialisedView
    elif spec.asset_type == DQAssetType.SNOWFLAKE_DYNAMIC_TABLE:
        asset_class = SnowflakeDynamicTable
    else:
        asset_class = Table  # Default fallback (includes TABLE and None)

    # Base parameters common to all rule types
    params = {
        "client": client,
        "asset": asset_class.ref_by_qualified_name(
            qualified_name=spec.asset_qualified_name
        ),
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

    # Create rule based on type using explicit creator methods
    if spec.rule_type == DQRuleType.CUSTOM_SQL:
        dq_rule = DataQualityRule.custom_sql_creator(**params)
    elif spec.rule_type == DQRuleType.ROW_COUNT:
        dq_rule = DataQualityRule.table_level_rule_creator(**params)
    elif spec.rule_type in {
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
    }:
        dq_rule = DataQualityRule.column_level_rule_creator(**params)
    else:
        raise ValueError(f"Unsupported rule type: {spec.rule_type}")

    # Add description if provided
    if spec.description:
        dq_rule.description = spec.description

    return dq_rule


def _build_rule_conditions(conditions: List[DQRuleCondition]) -> Any:
    """
    Build DQRuleConditionsBuilder from condition specifications.

    Args:
        conditions (List[DQRuleCondition]): List of rule condition models

    Returns:
        Built rule conditions object
    """
    builder = DQRuleConditionsBuilder()

    for condition in conditions:
        condition_type = DataQualityRuleTemplateConfigRuleConditions[condition.type]

        # Build condition parameters dynamically
        condition_params = {"type": condition_type}

        for key in ["value", "min_value", "max_value"]:
            value = getattr(condition, key)
            if value is not None:
                condition_params[key] = value

        builder.add_condition(**condition_params)

    return builder.build()


def schedule_dq_rules(
    schedules: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> DQRuleScheduleResponse:
    """
    Schedule data quality rule execution for one or multiple assets.

    Args:
        schedules: Either a single schedule specification or a list of specifications.

    Returns:
        DQRuleScheduleResponse: Response containing scheduled_count, scheduled_assets, and errors.
    """
    # Convert single schedule to list for consistent handling
    data = schedules if isinstance(schedules, list) else [schedules]

    result = DQRuleScheduleResponse()

    # Validate and parse specifications
    specs = []
    for idx, item in enumerate(data):
        try:
            spec = DQRuleScheduleSpecification(**item)
            specs.append(spec)
        except Exception as e:
            result.errors.append(f"Schedule {idx + 1} error: {str(e)}")
            logger.error(f"Error parsing schedule specification {idx + 1}: {e}")

    if not specs:
        logger.warning("No valid schedule specifications to create")
        return result

    # Get Atlan client
    client = get_atlan_client()

    # Schedule rules for each asset
    for spec in specs:
        try:
            if spec.asset_type == DQAssetType.TABLE:
                asset_cls = Table
            elif spec.asset_type == DQAssetType.VIEW:
                asset_cls = View
            elif spec.asset_type == DQAssetType.MATERIALIZED_VIEW:
                asset_cls = MaterialisedView
            elif spec.asset_type == DQAssetType.SNOWFLAKE_DYNAMIC_TABLE:
                asset_cls = SnowflakeDynamicTable
            else:
                raise ValueError(f"Unsupported asset type: {spec.asset_type.value}")

            client.asset.add_dq_rule_schedule(
                asset_type=asset_cls,
                asset_name=spec.asset_name,
                asset_qualified_name=spec.asset_qualified_name,
                schedule_crontab=spec.schedule_crontab,
                schedule_time_zone=spec.schedule_time_zone,
            )

            result.scheduled_assets.append(
                ScheduledAssetInfo(
                    asset_name=spec.asset_name,
                    asset_qualified_name=spec.asset_qualified_name,
                    schedule_crontab=spec.schedule_crontab,
                    schedule_time_zone=spec.schedule_time_zone,
                )
            )
            result.scheduled_count += 1

        except Exception as e:
            error_msg = f"Error scheduling {spec.asset_name}: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg)

    return result


def delete_dq_rules(
    rule_guids: Union[str, List[str]],
) -> DQRuleDeleteResponse:
    """
    Delete one or multiple data quality rules in Atlan.

    Args:
        rule_guids: Single rule GUID or list of rule GUIDs to delete.

    Returns:
        DQRuleDeleteResponse with deletion results and any errors.

    Example:
        # Delete single rule
        result = delete_dq_rules("rule-guid-123")

        # Delete multiple rules
        result = delete_dq_rules(["rule-guid-1", "rule-guid-2"])
    """
    # Convert single GUID to list for consistent handling
    data = rule_guids if isinstance(rule_guids, list) else [rule_guids]

    result = DQRuleDeleteResponse()

    # Validate and parse specifications
    specs = []
    for idx, item in enumerate(data):
        try:
            if isinstance(item, str):
                spec = DQRuleDeleteSpecification(rule_guid=item)
            else:
                spec = DQRuleDeleteSpecification(**item)
            specs.append(spec)
        except Exception as e:
            result.errors.append(f"Rule {idx + 1} error: {str(e)}")
            logger.error(f"Error parsing rule specification {idx + 1}: {e}")

    if not specs:
        logger.warning("No valid rule specifications to delete")
        return result

    # Get Atlan client
    client = get_atlan_client()

    # Delete each rule
    for spec in specs:
        try:
            response = client.asset.delete_by_guid(guid=spec.rule_guid)
            deleted_assets = response.assets_deleted(asset_type=DataQualityRule)

            if deleted_assets:
                result.deleted_rules.append(DeletedRuleInfo(rule_guid=spec.rule_guid))
                result.deleted_count += 1
                logger.info(f"Successfully deleted rule: {spec.rule_guid}")
            else:
                error_msg = f"No rule found with GUID: {spec.rule_guid}"
                result.errors.append(error_msg)
                logger.warning(error_msg)

        except Exception as e:
            error_msg = f"Error deleting rule {spec.rule_guid}: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg)

    return result

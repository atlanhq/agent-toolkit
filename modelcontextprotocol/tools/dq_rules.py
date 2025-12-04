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
    DQScheduleAssetType,
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


# Asset type class mapping for schedule operations
_SCHEDULE_ASSET_TYPE_MAP = {
    DQScheduleAssetType.TABLE: Table,
    DQScheduleAssetType.VIEW: View,
    DQScheduleAssetType.MATERIALIZED_VIEW: MaterialisedView,
    DQScheduleAssetType.SNOWFLAKE_DYNAMIC_TABLE: SnowflakeDynamicTable,
}


def schedule_dq_rules(
    schedules: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> DQRuleScheduleResponse:
    """
    Schedule data quality rule execution for one or multiple assets.

    This function configures automated scheduling for DQ rule execution on
    specified assets. The rules will run according to the provided cron schedule
    in the specified timezone.

    Args:
        schedules: Either a single schedule specification or a list of specifications.
            Each specification should contain:
            - asset_type (str): Type of asset ("Table", "View", "MaterialisedView",
              "SnowflakeDynamicTable")
            - asset_name (str): Display name of the asset
            - asset_qualified_name (str): Fully qualified name of the asset
            - schedule_crontab (str): Cron expression (5 fields: min hour day month weekday)
            - schedule_time_zone (str): Timezone (e.g., "UTC", "America/New_York")

    Returns:
        DQRuleScheduleResponse: Response containing:
            - scheduled_count: Number of schedules successfully created
            - scheduled_assets: List of ScheduledAssetInfo with details
            - errors: List of any error messages encountered

    Raises:
        ValueError: If schedule specification validation fails

    Examples:
        Schedule DQ rules for a single table:

        >>> result = schedule_dq_rules({
        ...     "asset_type": "Table",
        ...     "asset_name": "CUSTOMERS",
        ...     "asset_qualified_name": "default/snowflake/123/DB/SCHEMA/CUSTOMERS",
        ...     "schedule_crontab": "0 2 * * *",
        ...     "schedule_time_zone": "UTC"
        ... })

        Schedule DQ rules for multiple assets:

        >>> result = schedule_dq_rules([
        ...     {
        ...         "asset_type": "Table",
        ...         "asset_name": "ORDERS",
        ...         "asset_qualified_name": "default/snowflake/123/DB/SCHEMA/ORDERS",
        ...         "schedule_crontab": "0 3 * * *",
        ...         "schedule_time_zone": "America/New_York"
        ...     },
        ...     {
        ...         "asset_type": "View",
        ...         "asset_name": "DAILY_SUMMARY",
        ...         "asset_qualified_name": "default/snowflake/123/DB/SCHEMA/DAILY_SUMMARY",
        ...         "schedule_crontab": "30 4 * * *",
        ...         "schedule_time_zone": "UTC"
        ...     }
        ... ])
    """
    # Normalize input to list for consistent handling
    data = schedules if isinstance(schedules, list) else [schedules]
    logger.info(f"Scheduling data quality rules for {len(data)} asset(s)")
    logger.debug(f"Schedule specifications: {data}")

    result = DQRuleScheduleResponse()

    try:
        # Validate and parse all specifications first
        validated_specs: List[DQRuleScheduleSpecification] = []
        for idx, item in enumerate(data):
            try:
                spec = DQRuleScheduleSpecification(**item)
                validated_specs.append(spec)
            except ValueError as e:
                error_msg = f"Schedule {idx + 1} validation error: {str(e)}"
                result.errors.append(error_msg)
                logger.error(f"Validation failed for schedule {idx + 1}: {e}")
            except Exception as e:
                error_msg = f"Schedule {idx + 1} parsing error: {str(e)}"
                result.errors.append(error_msg)
                logger.error(f"Error parsing schedule specification {idx + 1}: {e}")

        if not validated_specs:
            logger.warning("No valid schedule specifications to process")
            return result

        # Get Atlan client
        client = get_atlan_client()

        # Process each validated specification
        for spec in validated_specs:
            try:
                logger.debug(
                    f"Creating schedule for {spec.asset_type.value} "
                    f"asset: {spec.asset_name}"
                )

                # Get the asset type class from mapping
                asset_cls = _SCHEDULE_ASSET_TYPE_MAP.get(spec.asset_type)
                if asset_cls is None:
                    raise ValueError(f"Unsupported asset type: {spec.asset_type.value}")

                # Schedule the data quality rules via Atlan client
                client.asset.add_dq_rule_schedule(
                    asset_type=asset_cls,
                    asset_name=spec.asset_name,
                    asset_qualified_name=spec.asset_qualified_name,
                    schedule_crontab=spec.schedule_crontab,
                    schedule_time_zone=spec.schedule_time_zone,
                )

                # Record successful scheduling
                result.scheduled_assets.append(
                    ScheduledAssetInfo(
                        asset_name=spec.asset_name,
                        asset_qualified_name=spec.asset_qualified_name,
                        schedule_crontab=spec.schedule_crontab,
                        schedule_time_zone=spec.schedule_time_zone,
                    )
                )
                result.scheduled_count += 1

                logger.info(
                    f"Successfully scheduled DQ rules for {spec.asset_name} "
                    f"({spec.schedule_crontab} {spec.schedule_time_zone})"
                )

            except Exception as e:
                error_msg = (
                    f"Error scheduling rules for '{spec.asset_name}' "
                    f"({spec.asset_qualified_name}): {str(e)}"
                )
                result.errors.append(error_msg)
                logger.error(error_msg)

        return result

    except Exception as e:
        error_msg = f"Unexpected error in schedule creation: {str(e)}"
        logger.error(error_msg)
        logger.exception("Exception details:")
        result.errors.append(error_msg)
        return result

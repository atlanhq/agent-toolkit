import logging
from enum import Enum
from typing import Optional, List, Union, Dict, Any

from pydantic import BaseModel, field_validator, model_validator

logger = logging.getLogger(__name__)


class CertificateStatus(str, Enum):
    """Enum for allowed certificate status values."""

    VERIFIED = "VERIFIED"
    DRAFT = "DRAFT"
    DEPRECATED = "DEPRECATED"


class UpdatableAttribute(str, Enum):
    """Enum for attributes that can be updated."""

    USER_DESCRIPTION = "user_description"
    CERTIFICATE_STATUS = "certificate_status"
    README = "readme"
    TERM = "term"


class TermOperation(str, Enum):
    """Enum for term operations on assets."""

    APPEND = "append"
    REPLACE = "replace"
    REMOVE = "remove"


class TermOperations(BaseModel):
    """Model for term operations on assets."""

    operation: TermOperation
    term_guids: List[str]


class UpdatableAsset(BaseModel):
    """Class representing an asset that can be updated."""

    guid: str
    name: str
    qualified_name: str
    type_name: str
    user_description: Optional[str] = None
    certificate_status: Optional[CertificateStatus] = None
    glossary_guid: Optional[str] = None


class Glossary(BaseModel):
    """Payload model for creating a glossary asset."""

    name: str
    user_description: Optional[str] = None
    certificate_status: Optional[CertificateStatus] = None


class GlossaryCategory(BaseModel):
    """Payload model for creating a glossary category asset."""

    name: str
    glossary_guid: str
    user_description: Optional[str] = None
    certificate_status: Optional[CertificateStatus] = None
    parent_category_guid: Optional[str] = None


class GlossaryTerm(BaseModel):
    """Payload model for creating a glossary term asset."""

    name: str
    glossary_guid: str
    user_description: Optional[str] = None
    certificate_status: Optional[CertificateStatus] = None
    category_guids: Optional[List[str]] = None


class DataDomainSpec(BaseModel):
    """Payload model for creating a Data Domain or Sub Domain asset."""

    name: str
    parent_domain_qualified_name: Optional[str] = (
        None  # if passed, will be created as a sub domain
    )
    user_description: Optional[str] = None
    certificate_status: Optional[CertificateStatus] = None


class DataProductSpec(BaseModel):
    """Payload model for creating a Data Product asset."""

    name: str
    domain_qualified_name: str
    asset_guids: List[str]  # Required: at least one asset GUID for data products
    user_description: Optional[str] = None
    certificate_status: Optional[CertificateStatus] = None

    @field_validator("asset_guids")
    @classmethod
    def validate_asset_guids(cls, v: List[str]) -> List[str]:
        """Validate that asset_guids is not empty."""
        if not v:
            raise ValueError(
                "Data products require at least one asset GUID. "
                "Please provide asset_guids to link assets to this product."
            )
        return v


class DQRuleCondition(BaseModel):
    """Model representing a single data quality rule condition."""

    type: (
        str  # Condition type (e.g., "STRING_LENGTH_BETWEEN", "REGEX_MATCH", "IN_LIST")
    )
    value: Optional[Union[str, List[str]]] = None  # Single value or list of values
    min_value: Optional[Union[int, float]] = None  # Minimum value for range conditions
    max_value: Optional[Union[int, float]] = None  # Maximum value for range conditions


class DQAssetType(str, Enum):
    """Enum for supported asset types for data quality rules."""

    TABLE = "Table"
    VIEW = "View"
    MATERIALIZED_VIEW = "MaterialisedView"
    SNOWFLAKE_DYNAMIC_TABLE = "SnowflakeDynamicTable"


class DQRuleType(str, Enum):
    """Enum for supported data quality rule types."""

    # Completeness checks
    NULL_COUNT = "Null Count"
    NULL_PERCENTAGE = "Null Percentage"
    BLANK_COUNT = "Blank Count"
    BLANK_PERCENTAGE = "Blank Percentage"

    # Statistical checks
    MIN_VALUE = "Min Value"
    MAX_VALUE = "Max Value"
    AVERAGE = "Average"
    STANDARD_DEVIATION = "Standard Deviation"

    # Uniqueness checks
    UNIQUE_COUNT = "Unique Count"
    DUPLICATE_COUNT = "Duplicate Count"

    # Validity checks
    REGEX = "Regex"
    STRING_LENGTH = "String Length"
    VALID_VALUES = "Valid Values"

    # Timeliness checks
    FRESHNESS = "Freshness"

    # Volume checks
    ROW_COUNT = "Row Count"

    # Custom checks
    CUSTOM_SQL = "Custom SQL"

    def get_rule_config(self) -> Dict[str, Any]:
        """
        Get complete configuration for this rule type.

        Returns:
            Dict containing:
                - creator_method: Name of the DataQualityRule creator method to use
                - requires_column: Whether this rule requires column_qualified_name
                - supports_conditions: Whether this rule supports conditional logic
        """
        # Custom SQL rules
        if self == DQRuleType.CUSTOM_SQL:
            return {
                "creator_method": "custom_sql_creator",
                "requires_column": False,
                "supports_conditions": False,
            }

        # Table-level rules
        if self == DQRuleType.ROW_COUNT:
            return {
                "creator_method": "table_level_rule_creator",
                "requires_column": False,
                "supports_conditions": False,
            }

        # Column-level rules with conditions
        if self in {
            DQRuleType.STRING_LENGTH,
            DQRuleType.REGEX,
            DQRuleType.VALID_VALUES,
        }:
            return {
                "creator_method": "column_level_rule_creator",
                "requires_column": True,
                "supports_conditions": True,
            }

        # Standard column-level rules
        return {
            "creator_method": "column_level_rule_creator",
            "requires_column": True,
            "supports_conditions": False,
        }


class DQRuleSpecification(BaseModel):
    """
    Comprehensive model for creating any type of data quality rule.

    Different rule types require different fields:
    - Column-level rules: require column_qualified_name
    - Table-level rules: only require asset_qualified_name
    - Custom SQL rules: require custom_sql, rule_name, dimension
    - Rules with conditions: require rule_conditions (String Length, Regex, Valid Values)
    """

    # Core identification
    rule_type: DQRuleType
    asset_qualified_name: str
    asset_type: Optional[DQAssetType] = DQAssetType.TABLE  # Default to Table

    # Column-level specific (required for most rule types except Row Count and Custom SQL)
    column_qualified_name: Optional[str] = None

    # Threshold configuration
    threshold_value: Optional[Union[int, float]] = None
    threshold_compare_operator: Optional[str] = None  # "EQUAL", "GREATER_THAN", etc.
    threshold_unit: Optional[str] = None  # "DAYS", "HOURS", "MINUTES"

    # Alert configuration
    alert_priority: Optional[str] = "NORMAL"  # "LOW", "NORMAL", "URGENT"

    # Custom SQL specific
    custom_sql: Optional[str] = None
    rule_name: Optional[str] = None
    dimension: Optional[str] = None  # "COMPLETENESS", "VALIDITY", etc.

    # Advanced configuration
    rule_conditions: Optional[List[DQRuleCondition]] = None
    row_scope_filtering_enabled: Optional[bool] = False
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_rule_requirements(self) -> "DQRuleSpecification":
        """
        Validate rule specification based on rule type requirements.

        Raises:
            ValueError: If required fields are missing for the rule type
        """
        errors = []
        config = self.rule_type.get_rule_config()

        # Check if column is required but missing
        if config["requires_column"] and not self.column_qualified_name:
            errors.append(f"{self.rule_type.value} requires column_qualified_name")

        # Custom SQL rules require specific fields
        if self.rule_type == DQRuleType.CUSTOM_SQL:
            if not self.custom_sql:
                errors.append("Custom SQL rules require custom_sql field")
            if not self.rule_name:
                errors.append("Custom SQL rules require rule_name field")
            if not self.dimension:
                errors.append("Custom SQL rules require dimension field")

        # Conditional rules should have conditions (warning only)
        if config["supports_conditions"] and not self.rule_conditions:
            logger.warning(f"{self.rule_type.value} rule created without conditions")

        # Freshness rules require threshold_unit
        if self.rule_type == DQRuleType.FRESHNESS and not self.threshold_unit:
            errors.append(
                "Freshness rules require threshold_unit (DAYS, HOURS, or MINUTES)"
            )

        # All rules require threshold_value
        if self.threshold_value is None:
            errors.append(f"{self.rule_type.value} requires threshold_value")

        if errors:
            raise ValueError("; ".join(errors))

        return self


class CreatedRuleInfo(BaseModel):
    """Model representing information about a created data quality rule."""

    guid: str
    qualified_name: str
    rule_type: Optional[str] = None


class DQRuleCreationResponse(BaseModel):
    """Response model for data quality rule creation operations."""

    created_count: int = 0
    created_rules: List[CreatedRuleInfo] = []
    errors: List[str] = []


class DQScheduleAssetType(str, Enum):
    """
    Enum for asset types that support data quality rule scheduling.

    These are the asset types where DQ rules can be scheduled to run
    automatically at specified intervals.
    """

    TABLE = "Table"
    VIEW = "View"
    MATERIALIZED_VIEW = "MaterialisedView"
    SNOWFLAKE_DYNAMIC_TABLE = "SnowflakeDynamicTable"


class DQRuleScheduleSpecification(BaseModel):
    """
    Specification model for scheduling data quality rules on an asset.

    This model defines the required parameters for scheduling DQ rule
    execution on a table, view, or other supported asset types.

    Attributes:
        asset_type: Type of asset (Table, View, etc.)
        asset_name: Display name of the asset
        asset_qualified_name: Fully qualified name of the asset in Atlan
        schedule_crontab: Cron expression defining the schedule (e.g., "0 0 * * *")
        schedule_time_zone: Timezone for the schedule (e.g., "UTC", "America/New_York")

    Example:
        ```python
        schedule = DQRuleScheduleSpecification(
            asset_type="Table",
            asset_name="CUSTOMERS",
            asset_qualified_name="default/snowflake/123/DB/SCHEMA/CUSTOMERS",
            schedule_crontab="0 2 * * *",  # Daily at 2 AM
            schedule_time_zone="UTC"
        )
        ```
    """

    asset_type: DQScheduleAssetType
    asset_name: str
    asset_qualified_name: str
    schedule_crontab: str
    schedule_time_zone: str

    @field_validator("schedule_crontab")
    @classmethod
    def validate_crontab(cls, v: str) -> str:
        """
        Validate the crontab expression format.

        A valid cron expression should have 5 fields:
        minute, hour, day of month, month, day of week.
        """
        parts = v.strip().split()
        if len(parts) != 5:
            raise ValueError(
                f"Invalid cron expression '{v}'. Expected 5 fields "
                "(minute hour day-of-month month day-of-week), got {len(parts)}."
            )
        return v.strip()

    @field_validator("schedule_time_zone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate that a non-empty timezone string is provided."""
        if not v or not v.strip():
            raise ValueError("schedule_time_zone cannot be empty")
        return v.strip()


class ScheduledAssetInfo(BaseModel):
    """
    Model representing information about a successfully scheduled asset.

    This is returned as part of the response to indicate which assets
    had their DQ rule schedules configured successfully.
    """

    asset_name: str
    asset_qualified_name: str
    schedule_crontab: str
    schedule_time_zone: str


class DQRuleScheduleResponse(BaseModel):
    """
    Response model for data quality rule scheduling operations.

    Contains the results of scheduling DQ rules on one or more assets,
    including success counts, details of scheduled assets, and any errors.

    Attributes:
        scheduled_count: Number of assets successfully scheduled
        scheduled_assets: List of successfully scheduled asset details
        errors: List of error messages for any failed scheduling attempts
    """

    scheduled_count: int = 0
    scheduled_assets: List[ScheduledAssetInfo] = []
    errors: List[str] = []

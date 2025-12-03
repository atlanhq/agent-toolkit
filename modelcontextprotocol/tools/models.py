import logging
from enum import Enum
from typing import Optional, List, Union, Dict, Any

from pydantic import BaseModel, model_validator

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


class DQAssetType(str, Enum):
    """Enum for supported asset types for data quality rules."""

    TABLE = "Table"
    VIEW = "View"
    MATERIALIZED_VIEW = "MaterialisedView"
    SNOWFLAKE_DYNAMIC_TABLE = "SnowflakeDynamicTable"


class DQRuleCondition(BaseModel):
    """Model representing a single data quality rule condition."""

    type: (
        str  # Condition type (e.g., "STRING_LENGTH_BETWEEN", "REGEX_MATCH", "IN_LIST")
    )
    value: Optional[Union[str, List[str]]] = None  # Single value or list of values
    min_value: Optional[Union[int, float]] = None  # Minimum value for range conditions
    max_value: Optional[Union[int, float]] = None  # Maximum value for range conditions


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
    asset_type: DQAssetType = DQAssetType.TABLE

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

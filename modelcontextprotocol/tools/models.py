from enum import Enum
from typing import Optional, List, Union

from pydantic import BaseModel


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


# ============================================================================
# Data Quality Rule Models
# ============================================================================


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


class DQAlertPriority(str, Enum):
    """Enum for data quality alert priority levels."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    URGENT = "URGENT"


class DQDimension(str, Enum):
    """Enum for data quality dimensions."""

    COMPLETENESS = "COMPLETENESS"
    VALIDITY = "VALIDITY"
    UNIQUENESS = "UNIQUENESS"
    TIMELINESS = "TIMELINESS"
    VOLUME = "VOLUME"
    ACCURACY = "ACCURACY"
    CONSISTENCY = "CONSISTENCY"


class DQThresholdCompareOperator(str, Enum):
    """Enum for threshold comparison operators."""

    EQUAL = "EQUAL"
    GREATER_THAN = "GREATER_THAN"
    GREATER_THAN_EQUAL = "GREATER_THAN_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_THAN_EQUAL = "LESS_THAN_EQUAL"
    BETWEEN = "BETWEEN"


class DQThresholdUnit(str, Enum):
    """Enum for threshold units (used in Freshness rules)."""

    DAYS = "DAYS"
    HOURS = "HOURS"
    MINUTES = "MINUTES"


class DQRuleConditionType(str, Enum):
    """Enum for rule condition types."""

    # String Length conditions
    STRING_LENGTH_EQUALS = "STRING_LENGTH_EQUALS"
    STRING_LENGTH_BETWEEN = "STRING_LENGTH_BETWEEN"
    STRING_LENGTH_GREATER_THAN = "STRING_LENGTH_GREATER_THAN"
    STRING_LENGTH_GREATER_THAN_EQUALS = "STRING_LENGTH_GREATER_THAN_EQUALS"
    STRING_LENGTH_LESS_THAN = "STRING_LENGTH_LESS_THAN"
    STRING_LENGTH_LESS_THAN_EQUALS = "STRING_LENGTH_LESS_THAN_EQUALS"

    # Regex conditions
    REGEX_MATCH = "REGEX_MATCH"
    REGEX_NOT_MATCH = "REGEX_NOT_MATCH"

    # Valid Values conditions
    IN_LIST = "IN_LIST"
    NOT_IN_LIST = "NOT_IN_LIST"


class DQRuleCondition(BaseModel):
    """Model for data quality rule conditions."""

    type: DQRuleConditionType
    value: Optional[Union[str, List[str]]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None


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

    # Column-level specific (required for most rule types except Row Count and Custom SQL)
    column_qualified_name: Optional[str] = None

    # Threshold configuration
    threshold_value: Optional[Union[int, float]] = None
    threshold_compare_operator: Optional[DQThresholdCompareOperator] = None
    threshold_unit: Optional[DQThresholdUnit] = None

    # Alert configuration
    alert_priority: Optional[DQAlertPriority] = DQAlertPriority.NORMAL

    # Custom SQL specific
    custom_sql: Optional[str] = None
    rule_name: Optional[str] = None
    dimension: Optional[DQDimension] = None

    # Advanced configuration
    rule_conditions: Optional[List[DQRuleCondition]] = None
    row_scope_filtering_enabled: Optional[bool] = False
    description: Optional[str] = None

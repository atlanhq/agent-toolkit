from enum import Enum
from typing import Optional, List, Union, Dict, Any

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
    threshold_compare_operator: Optional[str] = None  # "EQUAL", "GREATER_THAN", etc.
    threshold_unit: Optional[str] = None  # "DAYS", "HOURS", "MINUTES"

    # Alert configuration
    alert_priority: Optional[str] = "NORMAL"  # "LOW", "NORMAL", "URGENT"

    # Custom SQL specific
    custom_sql: Optional[str] = None
    rule_name: Optional[str] = None
    dimension: Optional[str] = None  # "COMPLETENESS", "VALIDITY", etc.

    # Advanced configuration
    rule_conditions: Optional[List[Dict[str, Any]]] = None
    row_scope_filtering_enabled: Optional[bool] = False
    description: Optional[str] = None

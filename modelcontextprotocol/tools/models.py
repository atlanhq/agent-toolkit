from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, field_validator, model_validator


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


class AssetHistoryRequest(BaseModel):
    """Request model for asset history retrieval."""

    guid: Optional[str] = None
    qualified_name: Optional[str] = None
    type_name: Optional[str] = None
    size: int = 10
    sort_order: str = "DESC"

    @model_validator(mode="after")
    def validate_asset_identifier(self) -> "AssetHistoryRequest":
        """Validate that either guid or qualified_name is provided."""
        if not self.guid and not self.qualified_name:
            raise ValueError("Either guid or qualified_name must be provided")

        if self.qualified_name and not self.type_name:
            raise ValueError("type_name is required when using qualified_name")

        return self

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """Validate sort order is either ASC or DESC."""
        if v not in ["ASC", "DESC"]:
            raise ValueError("sort_order must be either 'ASC' or 'DESC'")
        return v

    @field_validator("size")
    @classmethod
    def validate_size(cls, v: int) -> int:
        """Validate size is positive and within limits."""
        if v <= 0:
            raise ValueError("size must be greater than 0")
        if v > 50:
            raise ValueError("size cannot exceed 50")
        return v


class AuditEntry(BaseModel):
    """Model for a single audit entry."""

    guid: Optional[str] = None
    timestamp: Optional[int] = None
    action: Optional[str] = None
    user: Optional[str] = None
    detail: Optional[dict] = None

    class Config:
        """Pydantic config."""

        extra = "allow"  # Allow additional fields from audit detail


class AssetHistoryResponse(BaseModel):
    """Response model for asset history."""

    entity_audits: List[AuditEntry]
    count: int
    total_count: int
    errors: List[str] = []

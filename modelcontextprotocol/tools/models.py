from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, field_validator


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

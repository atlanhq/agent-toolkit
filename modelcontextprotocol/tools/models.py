from enum import Enum
from typing import Optional, List

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


class UpdatableAsset(BaseModel):
    """Class representing an asset that can be updated."""

    guid: str
    name: str
    qualified_name: str
    type_name: str
    user_description: Optional[str] = None
    certificate_status: Optional[CertificateStatus] = None


class GlossarySpecification(BaseModel):
    """Class representing specifications for creating a glossary."""

    name: str
    description: Optional[str] = None
    long_description: Optional[str] = None
    certificate_status: Optional[CertificateStatus] = None
    asset_icon: Optional[str] = None
    owner_users: Optional[List[str]] = None
    owner_groups: Optional[List[str]] = None


class GlossaryCategorySpecification(BaseModel):
    """Class representing specifications for creating a glossary category."""

    name: str
    glossary_guid: str
    description: Optional[str] = None
    long_description: Optional[str] = None
    certificate_status: Optional[CertificateStatus] = None
    parent_category_guid: Optional[str] = None
    owner_users: Optional[List[str]] = None
    owner_groups: Optional[List[str]] = None


class GlossaryTermSpecification(BaseModel):
    """Class representing specifications for creating a glossary term."""

    name: str
    glossary_guid: str
    alias: Optional[str] = None
    description: Optional[str] = None
    long_description: Optional[str] = None
    certificate_status: Optional[CertificateStatus] = None
    categories: Optional[List[str]] = None
    owner_users: Optional[List[str]] = None
    owner_groups: Optional[List[str]] = None

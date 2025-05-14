from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CertificateStatus(str, Enum):
    """Enum for allowed certificate status values."""

    VERIFIED = "VERIFIED"
    DRAFT = "DRAFT"
    DEPRECATED = "DEPRECATED"


class UpdatableAttribute(str, Enum):
    """Enum for attributes that can be updated."""

    USER_DESCRIPTION = "user_description"
    CERTIFICATE_STATUS = "certificate_status"


class UpdatableAsset(BaseModel):
    """Class representing an asset that can be updated."""

    guid: str = Field(..., description="The globally unique identifier of the asset.")
    name: str = Field(..., description="The human-readable name of the asset.")
    qualified_name: str = Field(..., description="The unique qualified name of the asset.")
    type_name: str = Field(..., description="The type name of the asset (e.g., Table, Column).")
    user_description: Optional[str] = Field(None, description="A user-defined description of the asset.")
    certificate_status: Optional[CertificateStatus] = Field(None, description="The certification status of the asset.")

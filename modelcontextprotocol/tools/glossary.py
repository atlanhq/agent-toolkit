"""Refactored glossary operations using modular utilities."""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List, Union

from pyatlan.model.assets import AtlasGlossary, AtlasGlossaryCategory, AtlasGlossaryTerm
from utils import parse_list_parameter
from .models import (
    CertificateStatus,
    GlossarySpecification,
    GlossaryCategorySpecification,
    GlossaryTermSpecification,
)
from utils import (
    process_certificate_status,
    process_owners,
    create_asset_with_error_handling,
    create_batch_processor,
)

logger = logging.getLogger(__name__)


def create_glossary_asset(
    name: str,
    description: Optional[str] = None,
    long_description: Optional[str] = None,
    certificate_status: Optional[Union[str, CertificateStatus]] = None,
    asset_icon: Optional[str] = None,
    owner_users: Optional[List[str]] = None,
    owner_groups: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Create a new AtlasGlossary asset in Atlan.

    Args:
        name (str): Name of the glossary (required).
        description (Optional[str]): Short description of the glossary.
        long_description (Optional[str]): Detailed description of the glossary.
        certificate_status (Optional[Union[str, CertificateStatus]]): Certification status.
        asset_icon (Optional[str]): Icon for the glossary.
        owner_users (Optional[List[str]]): List of user names who should own this glossary.
        owner_groups (Optional[List[str]]): List of group names who should own this glossary.

    Returns:
        Dict[str, Any]: Result dictionary with creation details.
    """

    def asset_creator() -> AtlasGlossary:
        # Create the glossary using the creator method
        glossary = AtlasGlossary.creator(name=name)

        # Set optional attributes
        glossary.description = description
        glossary.user_description = long_description

        # Process certificate status and owners using utilities
        process_certificate_status(glossary, certificate_status)
        process_owners(glossary, owner_users, owner_groups)

        return glossary

    return create_asset_with_error_handling(
        asset_creator=asset_creator,
        asset_name=name,
        asset_type="glossary",
    )


def create_glossary_category_asset(
    name: str,
    glossary_guid: str,
    description: Optional[str] = None,
    long_description: Optional[str] = None,
    certificate_status: Optional[Union[str, CertificateStatus]] = None,
    parent_category_guid: Optional[str] = None,
    owner_users: Optional[List[str]] = None,
    owner_groups: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Create a new AtlasGlossaryCategory asset in Atlan.

    Args:
        name (str): Name of the category (required).
        glossary_guid (str): GUID of the glossary this category belongs to (required).
        description (Optional[str]): Short description of the category.
        long_description (Optional[str]): Detailed description of the category.
        certificate_status (Optional[Union[str, CertificateStatus]]): Certification status.
        parent_category_guid (Optional[str]): GUID of the parent category if subcategory.
        owner_users (Optional[List[str]]): List of user names who should own this category.
        owner_groups (Optional[List[str]]): List of group names who should own this category.

    Returns:
        Dict[str, Any]: Result dictionary with creation details.
    """

    def asset_creator() -> AtlasGlossaryCategory:
        # Create a reference to the parent glossary
        anchor_glossary = AtlasGlossary.ref_by_guid(glossary_guid)

        # Create the category
        category = AtlasGlossaryCategory.creator(
            name=name,
            anchor=anchor_glossary,
            parent_category=(
                AtlasGlossaryCategory.ref_by_guid(parent_category_guid)
                if parent_category_guid
                else None
            ),
        )

        # Set optional attributes
        category.description = description
        category.user_description = long_description

        # Process certificate status and owners using utilities
        process_certificate_status(category, certificate_status)
        process_owners(category, owner_users, owner_groups)

        return category

    return create_asset_with_error_handling(
        asset_creator=asset_creator,
        asset_name=name,
        asset_type="glossary category",
        extra_result_fields={"glossary_guid": glossary_guid},
    )


def create_glossary_term_asset(
    name: str,
    glossary_guid: str,
    alias: Optional[str] = None,
    description: Optional[str] = None,
    long_description: Optional[str] = None,
    certificate_status: Optional[Union[str, CertificateStatus]] = None,
    categories: Optional[List[str]] = None,
    owner_users: Optional[List[str]] = None,
    owner_groups: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Create a new AtlasGlossaryTerm asset in Atlan.

    Args:
        name (str): Name of the term (required).
        glossary_guid (str): GUID of the glossary this term belongs to (required).
        alias (Optional[str]): An alias for the term.
        description (Optional[str]): Short description of the term.
        long_description (Optional[str]): Detailed description of the term.
        certificate_status (Optional[Union[str, CertificateStatus]]): Certification status.
        categories (Optional[List[str]]): List of category GUIDs this term belongs to.
        owner_users (Optional[List[str]]): List of user names who should own this term.
        owner_groups (Optional[List[str]]): List of group names who should own this term.

    Returns:
        Dict[str, Any]: Result dictionary with creation details.
    """

    def asset_creator() -> AtlasGlossaryTerm:
        # Build minimal references required for creation
        anchor_glossary = AtlasGlossary.ref_by_guid(glossary_guid)

        # Prepare category references if any
        category_refs = None
        normalised_categories = parse_list_parameter(categories)
        if normalised_categories:
            category_refs = [
                AtlasGlossaryCategory.ref_by_guid(cat_guid)
                for cat_guid in normalised_categories
            ]

        # Create the term
        term = AtlasGlossaryTerm.creator(
            name=name,
            anchor=anchor_glossary,
            categories=category_refs,
        )

        # Set optional attributes
        term.description = description
        term.user_description = long_description

        # Process certificate status and owners using utilities
        process_certificate_status(term, certificate_status)
        process_owners(term, owner_users, owner_groups)

        return term

    return create_asset_with_error_handling(
        asset_creator=asset_creator,
        asset_name=name,
        asset_type="glossary term",
        extra_result_fields={"glossary_guid": glossary_guid},
    )


# Helper functions to adapt specifications to individual creation functions
def _create_glossary_from_spec(spec: GlossarySpecification) -> Dict[str, Any]:
    """Adapter function to create glossary from specification."""
    return create_glossary_asset(
        name=spec.name,
        description=spec.description,
        long_description=spec.long_description,
        certificate_status=spec.certificate_status,
        asset_icon=spec.asset_icon,
        owner_users=spec.owner_users,
        owner_groups=spec.owner_groups,
    )


def _create_category_from_spec(spec: GlossaryCategorySpecification) -> Dict[str, Any]:
    """Adapter function to create category from specification."""
    return create_glossary_category_asset(
        name=spec.name,
        glossary_guid=spec.glossary_guid,
        description=spec.description,
        long_description=spec.long_description,
        certificate_status=spec.certificate_status,
        parent_category_guid=spec.parent_category_guid,
        owner_users=spec.owner_users,
        owner_groups=spec.owner_groups,
    )


def _create_term_from_spec(spec: GlossaryTermSpecification) -> Dict[str, Any]:
    """Adapter function to create term from specification."""
    return create_glossary_term_asset(
        name=spec.name,
        glossary_guid=spec.glossary_guid,
        alias=spec.alias,
        description=spec.description,
        long_description=spec.long_description,
        certificate_status=spec.certificate_status,
        categories=spec.categories,
        owner_users=spec.owner_users,
        owner_groups=spec.owner_groups,
    )


# Create batch processors using the generic utility
create_glossary_assets = create_batch_processor(
    single_creation_func=_create_glossary_from_spec,
    spec_class=GlossarySpecification,
    required_fields=["name"],
    item_type="glossary",
)

create_glossary_category_assets = create_batch_processor(
    single_creation_func=_create_category_from_spec,
    spec_class=GlossaryCategorySpecification,
    required_fields=["name", "glossary_guid"],
    item_type="category",
)

create_glossary_term_assets = create_batch_processor(
    single_creation_func=_create_term_from_spec,
    spec_class=GlossaryTermSpecification,
    required_fields=["name", "glossary_guid"],
    item_type="term",
)

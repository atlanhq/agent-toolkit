"""Refactored glossary operations using modular utilities."""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List, Union

from pyatlan.model.assets import AtlasGlossary, AtlasGlossaryCategory, AtlasGlossaryTerm
from utils.parameters import parse_list_parameter
from utils.glossary_utils import save_asset
from .models import (
    CertificateStatus,
    GlossarySpecification,
    GlossaryCategorySpecification,
    GlossaryTermSpecification,
)

logger = logging.getLogger(__name__)


def create_glossary_asset(
    name: str,
    description: Optional[str] = None,
    long_description: Optional[str] = None,
    certificate_status: Optional[Union[str, CertificateStatus]] = None,
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

        # Certificate status
        if certificate_status is not None:
            cs = (
                CertificateStatus(certificate_status)
                if isinstance(certificate_status, str)
                else certificate_status
            )
            glossary.certificate_status = cs.value

        # Owners
        users = parse_list_parameter(owner_users)
        if users:
            glossary.owner_users = set(users)

        groups = parse_list_parameter(owner_groups)
        if groups:
            glossary.owner_groups = set(groups)

        return glossary

    return save_asset(asset_creator())


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

        if certificate_status is not None:
            cs = (
                CertificateStatus(certificate_status)
                if isinstance(certificate_status, str)
                else certificate_status
            )
            category.certificate_status = cs.value

        users = parse_list_parameter(owner_users)
        if users:
            category.owner_users = set(users)

        groups = parse_list_parameter(owner_groups)
        if groups:
            category.owner_groups = set(groups)

        return category

    return save_asset(asset_creator(), extra={"glossary_guid": glossary_guid})


def create_glossary_term_asset(
    name: str,
    glossary_guid: str,
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

        if certificate_status is not None:
            cs = (
                CertificateStatus(certificate_status)
                if isinstance(certificate_status, str)
                else certificate_status
            )
            term.certificate_status = cs.value

        users = parse_list_parameter(owner_users)
        if users:
            term.owner_users = set(users)

        groups = parse_list_parameter(owner_groups)
        if groups:
            term.owner_groups = set(groups)

        return term

    return save_asset(asset_creator(), extra={"glossary_guid": glossary_guid})


def _normalize_input(
    raw: Union[
        Dict[str, Any],
        GlossarySpecification,
        List[Union[Dict[str, Any], GlossarySpecification]],
    ],
    spec_cls,
):
    """Return list of validated specification objects."""
    if isinstance(raw, list):
        data = raw
    else:
        data = [raw]

    specs: List[spec_cls] = []
    for item in data:
        if isinstance(item, spec_cls):
            specs.append(item)
        else:
            specs.append(spec_cls(**item))  # type: ignore[arg-type]
    return specs


def create_glossary_assets(
    glossaries: Union[
        Dict[str, Any],
        GlossarySpecification,
        List[Union[Dict[str, Any], GlossarySpecification]],
    ],
) -> Dict[str, Any]:
    """Create one or many glossaries and return a summary dictionary."""

    specs = _normalize_input(glossaries, GlossarySpecification)
    results: List[Dict[str, Any]] = []

    for idx, spec in enumerate(specs):
        res = create_glossary_asset(
            name=spec.name,
            description=spec.description,
            long_description=spec.long_description,
            certificate_status=spec.certificate_status,
            owner_users=spec.owner_users,
            owner_groups=spec.owner_groups,
        )
        res["index"] = idx
        results.append(res)

    success_count = sum(1 for r in results if r["success"])
    failed_count = len(results) - success_count

    return {
        "results": results,
        "successful_count": success_count,
        "failed_count": failed_count,
        "overall_success": failed_count == 0,
        "errors": [],
        "is_batch": len(specs) > 1,
    }


def create_glossary_category_assets(
    categories: Union[
        Dict[str, Any],
        GlossaryCategorySpecification,
        List[Union[Dict[str, Any], GlossaryCategorySpecification]],
    ],
) -> Dict[str, Any]:
    """Create glossary categories and return summary."""

    specs = _normalize_input(categories, GlossaryCategorySpecification)
    results: List[Dict[str, Any]] = []

    for idx, spec in enumerate(specs):
        res = create_glossary_category_asset(
            name=spec.name,
            glossary_guid=spec.glossary_guid,
            description=spec.description,
            long_description=spec.long_description,
            certificate_status=spec.certificate_status,
            parent_category_guid=spec.parent_category_guid,
            owner_users=spec.owner_users,
            owner_groups=spec.owner_groups,
        )
        res["index"] = idx
        results.append(res)

    success_count = sum(1 for r in results if r["success"])
    failed_count = len(results) - success_count

    return {
        "results": results,
        "successful_count": success_count,
        "failed_count": failed_count,
        "overall_success": failed_count == 0,
        "errors": [],
        "is_batch": len(specs) > 1,
    }


def create_glossary_term_assets(
    terms: Union[
        Dict[str, Any],
        GlossaryTermSpecification,
        List[Union[Dict[str, Any], GlossaryTermSpecification]],
    ],
) -> Dict[str, Any]:
    """Create glossary terms and return summary."""

    specs = _normalize_input(terms, GlossaryTermSpecification)
    results: List[Dict[str, Any]] = []

    for idx, spec in enumerate(specs):
        res = create_glossary_term_asset(
            name=spec.name,
            glossary_guid=spec.glossary_guid,
            description=spec.description,
            long_description=spec.long_description,
            certificate_status=spec.certificate_status,
            categories=spec.categories,
            owner_users=spec.owner_users,
            owner_groups=spec.owner_groups,
        )
        res["index"] = idx
        results.append(res)

    success_count = sum(1 for r in results if r["success"])
    failed_count = len(results) - success_count

    return {
        "results": results,
        "successful_count": success_count,
        "failed_count": failed_count,
        "overall_success": failed_count == 0,
        "errors": [],
        "is_batch": len(specs) > 1,
    }

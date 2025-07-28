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
    certificate_status: Optional[Union[str, CertificateStatus]] = None
) -> Dict[str, Any]:
    """
    Create a new AtlasGlossary asset in Atlan.

    Args:
        name (str): Name of the glossary (required).
        description (Optional[str]): Short description of the glossary.
        long_description (Optional[str]): Detailed description of the glossary.
        certificate_status (Optional[Union[str, CertificateStatus]]): Certification status.

    Returns:
        Dict[str, Any]: Result dictionary with creation details.
    """

    glossary = AtlasGlossary.creator(name=name)

    glossary.description = description
    glossary.user_description = long_description

    if certificate_status is not None:
        cs = (
            CertificateStatus(certificate_status)
            if isinstance(certificate_status, str)
            else certificate_status
        )
        glossary.certificate_status = cs.value

    return save_asset(glossary)


def create_glossary_category_asset(
    name: str,
    glossary_guid: str,
    description: Optional[str] = None,
    long_description: Optional[str] = None,
    certificate_status: Optional[Union[str, CertificateStatus]] = None,
    parent_category_guid: Optional[str] = None
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

    Returns:
        Dict[str, Any]: Result dictionary with creation details.
    """

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

    category.description = description
    category.user_description = long_description

    if certificate_status is not None:
        cs = (
            CertificateStatus(certificate_status)
            if isinstance(certificate_status, str)
            else certificate_status
        )
        category.certificate_status = cs.value

    return save_asset(category, extra={"glossary_guid": glossary_guid})


def create_glossary_term_asset(
    name: str,
    glossary_guid: str,
    description: Optional[str] = None,
    long_description: Optional[str] = None,
    certificate_status: Optional[Union[str, CertificateStatus]] = None,
    categories: Optional[List[str]] = None
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

    Returns:
        Dict[str, Any]: Result dictionary with creation details.
    """

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

    term = AtlasGlossaryTerm.creator(
        name=name,
        anchor=anchor_glossary,
        categories=category_refs,
    )
    term.description = description
    term.user_description = long_description

    if certificate_status is not None:
        cs = (
            CertificateStatus(certificate_status)
            if isinstance(certificate_status, str)
            else certificate_status
        )
        term.certificate_status = cs.value
    return save_asset(term, extra={"glossary_guid": glossary_guid})


def create_glossary_assets(
    glossaries: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Create one or many glossaries from dict payload(s) and return summary."""

    data = glossaries if isinstance(glossaries, list) else [glossaries]
    specs = [GlossarySpecification(**item) for item in data]

    results: List[Dict[str, Any]] = []

    for idx, spec in enumerate(specs):
        res = create_glossary_asset(
            name=spec.name,
            description=spec.description,
            long_description=spec.long_description,
            certificate_status=spec.certificate_status,
        )
        res["index"] = idx
        results.append(res)

    return {
        "results": results,
        "errors": [],
    }


def create_glossary_category_assets(
    categories: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Create one or many glossary categories from dict payload(s)."""

    data = categories if isinstance(categories, list) else [categories]
    specs = [GlossaryCategorySpecification(**item) for item in data]

    results: List[Dict[str, Any]] = []

    for idx, spec in enumerate(specs):
        res = create_glossary_category_asset(
            name=spec.name,
            glossary_guid=spec.glossary_guid,
            description=spec.description,
            long_description=spec.long_description,
            certificate_status=spec.certificate_status,
            parent_category_guid=spec.parent_category_guid,
        )
        res["index"] = idx
        results.append(res)

    return {
        "results": results,
        "errors": [],
    }


def create_glossary_term_assets(
    terms: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Create one or many glossary terms from dict payload(s)."""

    data = terms if isinstance(terms, list) else [terms]
    specs = [GlossaryTermSpecification(**item) for item in data]

    results: List[Dict[str, Any]] = []

    for idx, spec in enumerate(specs):
        res = create_glossary_term_asset(
            name=spec.name,
            glossary_guid=spec.glossary_guid,
            description=spec.description,
            long_description=spec.long_description,
            certificate_status=spec.certificate_status,
            categories=spec.categories,
        )
        res["index"] = idx
        results.append(res)

    return {
        "results": results,
        "errors": [],
    }

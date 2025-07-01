"""Glossary operations for creating glossaries, categories, and terms."""

from __future__ import annotations  # PEP 563 postponed evaluation of annotations

import logging
from typing import Dict, Any, Optional, List, Union

from client import get_atlan_client
from pyatlan.model.assets import AtlasGlossary, AtlasGlossaryCategory, AtlasGlossaryTerm
from pyatlan.model.enums import AtlanIcon
from utils import parse_list_parameter  # shared helper
from .models import CertificateStatus

# Configure logging
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
        certificate_status (Optional[Union[str, CertificateStatus]]): Certification status of the glossary.
            Can be "VERIFIED", "DRAFT", or "DEPRECATED".
        asset_icon (Optional[str]): Icon for the glossary (e.g., "BOOK_OPEN_TEXT").
        owner_users (Optional[List[str]]): List of user names who should own this glossary.
        owner_groups (Optional[List[str]]): List of group names who should own this glossary.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - guid: The GUID of the created glossary
            - name: The name of the created glossary
            - qualified_name: The qualified name of the created glossary
            - success: Boolean indicating if creation was successful
            - errors: List of any errors encountered
    """
    logger.info(f"Creating glossary asset: {name}")

    try:
        # Get Atlan client
        client = get_atlan_client()

        # Create the glossary using the creator method
        glossary = AtlasGlossary.creator(name=name)

        # Set optional attributes
        glossary.description = description

        glossary.user_description = long_description

        if isinstance(certificate_status, str):
            certificate_status = CertificateStatus(certificate_status)
        glossary.certificate_status = certificate_status.value

        # Normalise potential list-like inputs that might be JSON strings
        normalised_owner_users = parse_list_parameter(owner_users)
        if normalised_owner_users:
            glossary.owner_users = set(normalised_owner_users)

        normalised_owner_groups = parse_list_parameter(owner_groups)
        if normalised_owner_groups:
            glossary.owner_groups = set(normalised_owner_groups)

        # Save the glossary
        response = client.asset.save(glossary)

        # Extract the GUID from the response
        created_guid = None
        if response.guid_assignments:
            created_guid = list(response.guid_assignments.values())[0]

        result = {
            "guid": created_guid,
            "name": name,
            "qualified_name": glossary.qualified_name,
            "success": True,
            "errors": [],
        }

        logger.info(f"Successfully created glossary: {name} with GUID: {created_guid}")
        return result

    except Exception as e:
        error_msg = f"Error creating glossary '{name}': {str(e)}"
        logger.error(error_msg)
        return {
            "guid": None,
            "name": name,
            "qualified_name": None,
            "success": False,
            "errors": [error_msg],
        }


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
        certificate_status (Optional[Union[str, CertificateStatus]]): Certification status of the category.
            Can be "VERIFIED", "DRAFT", or "DEPRECATED".
        parent_category_guid (Optional[str]): GUID of the parent category if this is a subcategory.
        owner_users (Optional[List[str]]): List of user names who should own this category.
        owner_groups (Optional[List[str]]): List of group names who should own this category.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - guid: The GUID of the created category
            - name: The name of the created category
            - qualified_name: The qualified name of the created category
            - glossary_guid: The GUID of the parent glossary
            - success: Boolean indicating if creation was successful
            - errors: List of any errors encountered
    """
    logger.info(f"Creating glossary category: {name} in glossary: {glossary_guid}")

    try:
        # Get Atlan client
        client = get_atlan_client()

        # Create a reference to the parent glossary using its GUID
        anchor_glossary = AtlasGlossary.ref_by_guid(glossary_guid)

        # Create the category using the correct creator signature
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

        if isinstance(certificate_status, str):
            certificate_status = CertificateStatus(certificate_status)
        category.certificate_status = certificate_status.value

        normalised_owner_users = parse_list_parameter(owner_users)
        if normalised_owner_users:
            category.owner_users = set(normalised_owner_users)

        normalised_owner_groups = parse_list_parameter(owner_groups)
        if normalised_owner_groups:
            category.owner_groups = set(normalised_owner_groups)

        # Save the category
        response = client.asset.save(category)

        # Extract the GUID from the response
        created_guid = None
        if response.guid_assignments:
            created_guid = list(response.guid_assignments.values())[0]

        result = {
            "guid": created_guid,
            "name": name,
            "qualified_name": category.qualified_name,
            "glossary_guid": glossary_guid,
            "success": True,
            "errors": [],
        }

        logger.info(
            f"Successfully created glossary category: {name} with GUID: {created_guid}"
        )
        return result

    except Exception as e:
        error_msg = f"Error creating glossary category '{name}': {str(e)}"
        logger.error(error_msg)
        return {
            "guid": None,
            "name": name,
            "qualified_name": None,
            "glossary_guid": glossary_guid,
            "success": False,
            "errors": [error_msg],
        }


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
        certificate_status (Optional[Union[str, CertificateStatus]]): Certification status of the term.
            Can be "VERIFIED", "DRAFT", or "DEPRECATED".
        categories (Optional[List[str]]): List of category GUIDs this term belongs to.
        owner_users (Optional[List[str]]): List of user names who should own this term.
        owner_groups (Optional[List[str]]): List of group names who should own this term.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - guid: The GUID of the created term
            - name: The name of the created term
            - qualified_name: The qualified name of the created term
            - glossary_guid: The GUID of the parent glossary
            - success: Boolean indicating if creation was successful
            - errors: List of any errors encountered
    """
    logger.info(f"Creating glossary term: {name} in glossary: {glossary_guid}")

    try:
        # Get Atlan client
        client = get_atlan_client()

        # Build minimal references required for creation
        anchor_glossary = AtlasGlossary.ref_by_guid(glossary_guid)

        # Prepare category references (if any) upfront so they can be sent through the creator call itself.
        category_refs: Optional[List[AtlasGlossaryCategory]] = None

        normalised_categories = parse_list_parameter(categories)
        if normalised_categories:
            category_refs = [
                AtlasGlossaryCategory.ref_by_guid(cat_guid)
                for cat_guid in normalised_categories
            ]

        # Create the term using the creator helper, passing anchor and (optionally) categories directly.
        if category_refs:
            term = AtlasGlossaryTerm.creator(
                name=name,
                anchor=anchor_glossary,
                categories=category_refs,
            )
        else:
            term = AtlasGlossaryTerm.creator(name=name, anchor=anchor_glossary)

        # Set optional attributes
        term.description = description

        term.user_description = long_description

        if isinstance(certificate_status, str):
            certificate_status = CertificateStatus(certificate_status)
        term.certificate_status = certificate_status.value

        normalised_owner_users = parse_list_parameter(owner_users)
        if normalised_owner_users:
            term.owner_users = set(normalised_owner_users)

        normalised_owner_groups = parse_list_parameter(owner_groups)
        if normalised_owner_groups:
            term.owner_groups = set(normalised_owner_groups)

        # Save the term first, then handle relationships that require both terms to exist
        response = client.asset.save(term)

        # Extract the GUID from the response
        created_guid = None
        if response.guid_assignments:
            created_guid = list(response.guid_assignments.values())[0]

        result = {
            "guid": created_guid,
            "name": name,
            "qualified_name": term.qualified_name,
            "glossary_guid": glossary_guid,
            "success": True,
            "errors": [],
        }

        logger.info(
            f"Successfully created glossary term: {name} with GUID: {created_guid}"
        )
        return result

    except Exception as e:
        error_msg = f"Error creating glossary term '{name}': {str(e)}"
        logger.error(error_msg)
        return {
            "guid": None,
            "name": name,
            "qualified_name": None,
            "glossary_guid": glossary_guid,
            "success": False,
            "errors": [error_msg],
        }

"""Glossary operations for creating glossaries, categories, and terms."""

from __future__ import annotations  # PEP 563 postponed evaluation of annotations

import json
import logging
from typing import Dict, Any, Optional, List, Union, Iterable, cast

from client import get_atlan_client
from pyatlan.model.assets import AtlasGlossary, AtlasGlossaryCategory, AtlasGlossaryTerm
from pyatlan.model.enums import AtlanIcon
from .models import CertificateStatus

# Configure logging
logger = logging.getLogger(__name__)


def _normalize_to_list(value: Optional[Union[str, Iterable[str]]]) -> Optional[List[str]]:  # noqa: D401
    """Return ``value`` as a list of strings.

    This helper attempts to be forgiving with the shapes we receive from the LLM
    front-end.  In particular, some models (for example, *Claude*) may serialise
    Python lists as **JSON-encoded strings** instead of sending them as native
    lists.  This normaliser handles the following cases gracefully:

    1. ``None`` – the value is returned unchanged.
    2. ``list`` / ``set`` / ``tuple`` of strings – converted to ``list``.
    3. A single plain string – wrapped in a one-item ``list``.
    4. A JSON string that represents a list – parsed into a list.

    Args:
        value: The incoming parameter that is expected to contain one or more
            strings.

    Returns:
        A list of strings or ``None`` if *value* is falsy.

    Raises:
        TypeError: If *value* is of an unexpected type or if a JSON string does
            not decode into a list of strings.
    """

    if not value:
        # Covers both None and empty containers / empty strings.
        return None

    # If it's already an iterable of strings (but *not* a str), convert to list.
    if isinstance(value, (list, set, tuple)):
        return list(cast(Iterable[str], value))

    # If it's a bare string we need to inspect further.
    if isinstance(value, str):
        stripped = value.strip()

        # Attempt to parse JSON-encoded list.
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                parsed = json.loads(stripped)
                if not isinstance(parsed, list):
                    raise TypeError(
                        "JSON string did not decode into a list – got "
                        f"{type(parsed).__name__}."
                    )
                # Ensure *all* items are strings.
                if not all(isinstance(item, str) for item in parsed):
                    raise TypeError("Decoded JSON list contains non-string items.")
                return parsed
            except json.JSONDecodeError as exc:  # pragma: no cover – defensive.
                logger.debug("Value %s is not valid JSON: %s", value, exc)
                # Attempt a graceful, best-effort parse for malformed JSON-like input.

                # Remove the surrounding square brackets if present so that we can
                # split on commas: "[foo, bar]" → "foo, bar".
                inner = stripped[1:-1] if stripped.startswith("[") and stripped.endswith("]") else stripped

                # Split on commas **that are not inside quotes** (basic heuristic).
                # We intentionally keep this simple – it does not try to parse
                # escaped quotes or nested structures because the expected input
                # is a *flat* list of names.
                cleaned_parts: List[str] = []
                for raw_part in inner.split(","):
                    part = raw_part.strip().strip("\"").strip("'")
                    if part:
                        cleaned_parts.append(part)
                parts = cleaned_parts

                if parts:
                    return parts

        # Final fallback – treat the entire value as a single string item.
        return [stripped]

    raise TypeError(
        "Expected None, string, or iterable of strings for list-like parameter; "
        f"got {type(value).__name__}."
    )


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
        if description:
            glossary.description = description

        if long_description:
            glossary.user_description = long_description

        if certificate_status:
            # Convert string to CertificateStatus enum if needed
            if isinstance(certificate_status, str):
                certificate_status = CertificateStatus(certificate_status)
            glossary.certificate_status = certificate_status.value

        if asset_icon:
            try:
                # Convert string to AtlanIcon enum
                icon_enum = getattr(AtlanIcon, asset_icon.upper())
                glossary.asset_icon = icon_enum
            except AttributeError:

                logger.warning(f"Invalid icon: {asset_icon}. Using default.")
        # Normalise potential list-like inputs that might be JSON strings
        normalised_owner_users = _normalize_to_list(owner_users)
        if normalised_owner_users:
            glossary.owner_users = set(normalised_owner_users)

        normalised_owner_groups = _normalize_to_list(owner_groups)
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
        if description:
            category.description = description

        if long_description:
            category.user_description = long_description

        if certificate_status:
            # Convert string to CertificateStatus enum if needed
            if isinstance(certificate_status, str):
                certificate_status = CertificateStatus(certificate_status)
            category.certificate_status = certificate_status.value

        normalised_owner_users = _normalize_to_list(owner_users)
        if normalised_owner_users:
            category.owner_users = set(normalised_owner_users)

        normalised_owner_groups = _normalize_to_list(owner_groups)
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

        normalised_categories = _normalize_to_list(categories)
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
        if description:
            term.description = description

        if long_description:
            term.user_description = long_description

        if certificate_status:
            # Convert string to CertificateStatus enum if needed
            if isinstance(certificate_status, str):
                certificate_status = CertificateStatus(certificate_status)
            term.certificate_status = certificate_status.value

        normalised_owner_users = _normalize_to_list(owner_users)
        if normalised_owner_users:
            term.owner_users = set(normalised_owner_users)

        normalised_owner_groups = _normalize_to_list(owner_groups)
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

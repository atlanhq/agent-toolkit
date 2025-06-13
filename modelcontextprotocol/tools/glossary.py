"""Glossary operations for creating glossaries, categories, and terms."""

import logging
from typing import Dict, Any, Optional, List, Union

from client import get_atlan_client
from pyatlan.model.assets import AtlasGlossary, AtlasGlossaryCategory, AtlasGlossaryTerm
from pyatlan.model.enums import AtlanIcon
from .models import CertificateStatus

# Configure logging
logger = logging.getLogger(__name__)


def create_glossary_asset(
    name: str,
    description: Optional[str] = None,
    long_description: Optional[str] = None,
    certificate_status: Optional[Union[str, CertificateStatus]] = None,
    asset_icon: Optional[str] = None,
    owner_users: Optional[Union[str, List[str]]] = None,
    owner_groups: Optional[Union[str, List[str]]] = None,
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
        owner_users (Optional[Union[str, List[str]]]): User name(s) who should own this glossary.
            Can be a single string or a list of strings.
        owner_groups (Optional[Union[str, List[str]]]): Group name(s) who should own this glossary.
            Can be a single string or a list of strings.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - guid: The GUID of the created glossary
            - name: The name of the created glossary
            - qualified_name: The qualified name of the created glossary
            - success: Boolean indicating if creation was successful
            - errors: List of any errors encountered

    Examples:
        # Create a basic glossary
        glossary = create_glossary_asset(
            name="Business Terms",
            description="Common business terminology used across the organization"
        )

        # Create a glossary with icon, certification, and ownership
        glossary = create_glossary_asset(
            name="Data Quality Glossary",
            description="Terms related to data quality standards",
            long_description="This glossary contains comprehensive definitions of data quality metrics, standards, and processes used throughout our data platform.",
            certificate_status="VERIFIED",
            asset_icon="BOOK_OPEN_TEXT",
            owner_users=["john.doe", "jane.smith"],  # List of users
            owner_groups="data-stewards"  # Single group (can also be a list)
        )
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

        if owner_users:
            # Handle both single string and list of strings
            if isinstance(owner_users, str):
                glossary.owner_users = {owner_users}
            else:
                glossary.owner_users = set(owner_users)

        if owner_groups:
            # Handle both single string and list of strings
            group_names = []
            if isinstance(owner_groups, str):
                group_names = [owner_groups]
            else:
                group_names = list(owner_groups)

            # Look up group GUIDs by name
            group_guids = set()
            for group_name in group_names:
                try:
                    # Search for existing group by name
                    groups_result = client.group.get_by_name(group_name)
                    if groups_result.records and len(groups_result.records) > 0:
                        # Get the first matching group's GUID
                        group_guid = groups_result.records[0].guid
                        group_guids.add(group_guid)
                        logger.info(
                            f"Found existing group '{group_name}' with GUID: {group_guid}"
                        )
                    else:
                        logger.warning(
                            f"Group '{group_name}' not found in Atlan. Skipping."
                        )
                except Exception as e:
                    logger.error(f"Error looking up group '{group_name}': {str(e)}")

            # Set the group GUIDs instead of names
            if group_guids:
                glossary.owner_groups = group_guids

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
    owner_users: Optional[Union[str, List[str]]] = None,
    owner_groups: Optional[Union[str, List[str]]] = None,
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
        owner_users (Optional[Union[str, List[str]]]): User name(s) who should own this category.
            Can be a single string or a list of strings.
        owner_groups (Optional[Union[str, List[str]]]): Group name(s) who should own this category.
            Can be a single string or a list of strings.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - guid: The GUID of the created category
            - name: The name of the created category
            - qualified_name: The qualified name of the created category
            - glossary_guid: The GUID of the parent glossary
            - success: Boolean indicating if creation was successful
            - errors: List of any errors encountered

    Examples:
        # Create a basic category
        category = create_glossary_category_asset(
            name="Customer Data",
            glossary_guid="glossary-guid-here",
            description="Terms related to customer information and attributes"
        )

        # Create a subcategory with detailed information and certification
        subcategory = create_glossary_category_asset(
            name="Customer Demographics",
            glossary_guid="glossary-guid-here",
            parent_category_guid="parent-category-guid-here",
            description="Terms specific to customer demographic information",
            long_description="This category contains terms that define various demographic attributes of customers such as age groups, income brackets, geographic regions, etc.",
            certificate_status="VERIFIED",
            owner_users="data.steward",  # Single user (can also be a list)
            owner_groups=["customer-analytics-team"]  # List of groups
        )
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

        if owner_users:
            # Handle both single string and list of strings
            if isinstance(owner_users, str):
                category.owner_users = {owner_users}
            else:
                category.owner_users = set(owner_users)

        if owner_groups:
            # Handle both single string and list of strings
            group_names = []
            if isinstance(owner_groups, str):
                group_names = [owner_groups]
            else:
                group_names = list(owner_groups)

            # Look up group GUIDs by name
            group_guids = set()
            for group_name in group_names:
                try:
                    # Search for existing group by name
                    groups_result = client.group.get_by_name(group_name)
                    if groups_result.records and len(groups_result.records) > 0:
                        # Get the first matching group's GUID
                        group_guid = groups_result.records[0].guid
                        group_guids.add(group_guid)
                        logger.info(
                            f"Found existing group '{group_name}' with GUID: {group_guid}"
                        )
                    else:
                        logger.warning(
                            f"Group '{group_name}' not found in Atlan. Skipping."
                        )
                except Exception as e:
                    logger.error(f"Error looking up group '{group_name}': {str(e)}")

            # Set the group GUIDs instead of names
            if group_guids:
                category.owner_groups = group_guids

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
    description: Optional[str] = None,
    long_description: Optional[str] = None,
    certificate_status: Optional[Union[str, CertificateStatus]] = None,
    categories: Optional[List[str]] = None,
    related_terms: Optional[List[str]] = None,
    synonyms: Optional[List[str]] = None,
    antonyms: Optional[List[str]] = None,
    preferred_terms: Optional[List[str]] = None,
    replacement_terms: Optional[List[str]] = None,
    owner_users: Optional[Union[str, List[str]]] = None,
    owner_groups: Optional[Union[str, List[str]]] = None,
) -> Dict[str, Any]:
    """
    Create a new AtlasGlossaryTerm asset in Atlan.

    Args:
        name (str): Name of the term (required).
        glossary_guid (str): GUID of the glossary this term belongs to (required).
        description (Optional[str]): Short description of the term.
        long_description (Optional[str]): Detailed description of the term.
        certificate_status (Optional[Union[str, CertificateStatus]]): Certification status of the term.
            Can be "VERIFIED", "DRAFT", or "DEPRECATED".
        categories (Optional[List[str]]): List of category GUIDs this term belongs to.
        related_terms (Optional[List[str]]): List of related term GUIDs.
        synonyms (Optional[List[str]]): List of synonym term GUIDs.
        antonyms (Optional[List[str]]): List of antonym term GUIDs.
        preferred_terms (Optional[List[str]]): List of preferred term GUIDs.
        replacement_terms (Optional[List[str]]): List of replacement term GUIDs.
        owner_users (Optional[Union[str, List[str]]]): User name(s) who should own this term.
            Can be a single string or a list of strings.
        owner_groups (Optional[Union[str, List[str]]]): Group name(s) who should own this term.
            Can be a single string or a list of strings.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - guid: The GUID of the created term
            - name: The name of the created term
            - qualified_name: The qualified name of the created term
            - glossary_guid: The GUID of the parent glossary
            - success: Boolean indicating if creation was successful
            - errors: List of any errors encountered

    Examples:
        # Create a basic term
        term = create_glossary_term_asset(
            name="Customer",
            glossary_guid="glossary-guid-here",
            description="An individual or organization that purchases goods or services"
        )

        # Create a comprehensive term with relationships and certification
        term = create_glossary_term_asset(
            name="Annual Recurring Revenue",
            glossary_guid="glossary-guid-here",
            description="The yearly value of recurring revenue from customers",
            long_description="Annual Recurring Revenue (ARR) is a key metric that represents the yearly value of recurring revenue streams. It includes subscription fees and other predictable revenue sources, excluding one-time payments or variable fees.",
            certificate_status="VERIFIED",
            categories=["category-guid-1", "category-guid-2"],
            synonyms=["synonym-term-guid"],
            related_terms=["related-term-guid-1", "related-term-guid-2"],
            owner_users="revenue.analyst",  # Single user (can also be a list)
            owner_groups=["finance-team"]  # List of groups
        )
    """
    logger.info(f"Creating glossary term: {name} in glossary: {glossary_guid}")

    try:
        # Get Atlan client
        client = get_atlan_client()

        # Create the term using the creator method
        term = AtlasGlossaryTerm.creator(name=name, glossary_guid=glossary_guid)

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

        if categories:
            # Set categories - create references to the category GUIDs
            category_refs = [
                AtlasGlossaryCategory.ref_by_guid(cat_guid) for cat_guid in categories
            ]
            term.categories = set(category_refs)

        if owner_users:
            # Handle both single string and list of strings
            if isinstance(owner_users, str):
                term.owner_users = {owner_users}
            else:
                term.owner_users = set(owner_users)

        if owner_groups:
            # Handle both single string and list of strings
            group_names = []
            if isinstance(owner_groups, str):
                group_names = [owner_groups]
            else:
                group_names = list(owner_groups)

            # Look up group GUIDs by name
            group_guids = set()
            for group_name in group_names:
                try:
                    # Search for existing group by name
                    groups_result = client.group.get_by_name(group_name)
                    if groups_result.records and len(groups_result.records) > 0:
                        # Get the first matching group's GUID
                        group_guid = groups_result.records[0].guid
                        group_guids.add(group_guid)
                        logger.info(
                            f"Found existing group '{group_name}' with GUID: {group_guid}"
                        )
                    else:
                        logger.warning(
                            f"Group '{group_name}' not found in Atlan. Skipping."
                        )
                except Exception as e:
                    logger.error(f"Error looking up group '{group_name}': {str(e)}")

            # Set the group GUIDs instead of names
            if group_guids:
                term.owner_groups = group_guids

        # Save the term first, then handle relationships that require both terms to exist
        response = client.asset.save(term)

        # Extract the GUID from the response
        created_guid = None
        if response.guid_assignments:
            created_guid = list(response.guid_assignments.values())[0]

        # Handle term relationships (these require the term to exist first)
        if created_guid and any(
            [related_terms, synonyms, antonyms, preferred_terms, replacement_terms]
        ):
            try:
                # Retrieve the created term to set relationships
                created_term = client.asset.get_by_guid(created_guid, AtlasGlossaryTerm)

                if related_terms:
                    related_refs = [
                        AtlasGlossaryTerm.ref_by_guid(term_guid)
                        for term_guid in related_terms
                    ]
                    created_term.see_also = set(related_refs)

                if synonyms:
                    synonym_refs = [
                        AtlasGlossaryTerm.ref_by_guid(term_guid)
                        for term_guid in synonyms
                    ]
                    created_term.synonyms = set(synonym_refs)

                if antonyms:
                    antonym_refs = [
                        AtlasGlossaryTerm.ref_by_guid(term_guid)
                        for term_guid in antonyms
                    ]
                    created_term.antonyms = set(antonym_refs)

                if preferred_terms:
                    preferred_refs = [
                        AtlasGlossaryTerm.ref_by_guid(term_guid)
                        for term_guid in preferred_terms
                    ]
                    created_term.preferred_terms = set(preferred_refs)

                if replacement_terms:
                    replacement_refs = [
                        AtlasGlossaryTerm.ref_by_guid(term_guid)
                        for term_guid in replacement_terms
                    ]
                    created_term.replacement_terms = set(replacement_refs)

                # Save the updated term with relationships
                client.asset.save(created_term)
                logger.info(f"Successfully updated term relationships for: {name}")

            except Exception as rel_error:
                logger.warning(
                    f"Term created but failed to set relationships: {str(rel_error)}"
                )

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

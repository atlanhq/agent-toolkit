from __future__ import annotations
import logging
from typing import Dict, Any, List, Union

from pyatlan.model.assets import (
    AtlasGlossary,
    AtlasGlossaryCategory,
    AtlasGlossaryTerm,
    Asset,
)
from utils.parameters import parse_list_parameter
from client import get_atlan_client
from .models import (
    CertificateStatus,
    Glossary,
    GlossaryCategory,
    GlossaryTerm,
)

logger = logging.getLogger(__name__)


def save_assets(assets: List[Asset]) -> Dict[str, Any]:
    """
    Common bulk save and response processing for any asset type.

    Args:
        assets (List[Asset]): List of Asset objects to save.

    Returns:
        Dict[str, Any]: Dictionary containing results list with success/failure info for each asset.

    Raises:
        Exception: If there's an error saving the assets.
    """
    logger.info(f"Starting bulk save operation for {len(assets)} assets")
    logger.debug(f"Asset types: {[type(asset).__name__ for asset in assets]}")

    client = get_atlan_client()
    response = client.asset.save(assets)
    results: List[Dict[str, Any]] = []
    created_assets = response.mutated_entities.CREATE

    logger.info(f"Save operation completed, processing {len(created_assets)} results")

    for i, created_asset in enumerate(created_assets):
        if created_asset and created_asset.guid:
            logger.debug(f"Successfully created asset {i}: {created_asset.guid}")
            result = {
                "guid": created_asset.guid,
                "name": created_asset.name if created_asset else assets[i].name,
                "qualified_name": created_asset.qualified_name,
                "success": True,
            }

            if hasattr(created_asset, "anchor") and created_asset.anchor:
                result["glossary_guid"] = created_asset.anchor.guid
            if (
                hasattr(created_asset, "parent_category")
                and created_asset.parent_category
            ):
                result["parent_category_guid"] = created_asset.parent_category.guid
            if hasattr(created_asset, "categories") and created_asset.categories:
                result["category_guids"] = [
                    cat.guid for cat in created_asset.categories if cat.guid
                ]

            results.append(result)
        else:
            logger.warning(f"Failed to create asset {i}: {assets[i].name}")
            results.append(
                {
                    "guid": None,
                    "name": created_asset.name if created_asset else assets[i].name,
                    "qualified_name": None,
                    "success": False,
                }
            )

    logger.info(
        f"Bulk save completed: {sum(1 for r in results if r['success'])} successful, {sum(1 for r in results if not r['success'])} failed"
    )
    return {"results": results}


def create_glossary_assets(
    glossaries: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Create one or multiple AtlasGlossary assets in Atlan.

    Args:
        glossaries (Union[Dict[str, Any], List[Dict[str, Any]]]): Either a single glossary
            specification (dict) or a list of glossary specifications. Each specification
            can be a dictionary containing:
            - name (str): Name of the glossary (required)
            - user_description (str, optional): Detailed description of the glossary
              proposed by the user
            - certificate_status (str, optional): Certification status
              ("VERIFIED", "DRAFT", or "DEPRECATED")

    Returns:
        Dict[str, Any]: Dictionary containing results list with details for each glossary
            creation attempt:
            - guid: The GUID of the created glossary (if successful)
            - name: The name of the glossary
            - qualified_name: The qualified name of the created glossary (if successful)
            - success: Boolean indicating if creation was successful

    Raises:
        Exception: If there's an error creating the glossary assets.
    """
    data = glossaries if isinstance(glossaries, list) else [glossaries]
    logger.info(f"Creating {len(data)} glossary asset(s)")
    logger.debug(f"Glossary specifications: {data}")

    specs = [Glossary(**item) for item in data]

    assets: List[AtlasGlossary] = []
    for spec in specs:
        logger.debug(f"Creating AtlasGlossary for: {spec.name}")
        glossary = AtlasGlossary.creator(name=spec.name)
        glossary.user_description = spec.user_description
        if spec.certificate_status is not None:
            cs = (
                CertificateStatus(spec.certificate_status)
                if isinstance(spec.certificate_status, str)
                else spec.certificate_status
            )
            glossary.certificate_status = cs.value
            logger.debug(f"Set certificate status for {spec.name}: {cs.value}")
        assets.append(glossary)

    return save_assets(assets)


def create_glossary_category_assets(
    categories: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Create one or multiple AtlasGlossaryCategory assets in Atlan.

    Args:
        categories (Union[Dict[str, Any], List[Dict[str, Any]]]): Either a single category
            specification (dict) or a list of category specifications. Each specification
            can be a dictionary containing:
            - name (str): Name of the category (required)
            - glossary_guid (str): GUID of the glossary this category belongs to (required)
            - user_description (str, optional): Detailed description of the category
              proposed by the user
            - certificate_status (str, optional): Certification status
              ("VERIFIED", "DRAFT", or "DEPRECATED")
            - parent_category_guid (str, optional): GUID of the parent category if this
              is a subcategory

    Returns:
        Dict[str, Any]: Dictionary containing results list with details for each category
            creation attempt:
            - guid: The GUID of the created category (if successful)
            - name: The name of the category
            - qualified_name: The qualified name of the created category (if successful)
            - glossary_guid: The GUID of the parent glossary (if available)
            - parent_category_guid: The GUID of the parent category (if subcategory)
            - success: Boolean indicating if creation was successful

    Raises:
        Exception: If there's an error creating the glossary category assets.
    """
    data = categories if isinstance(categories, list) else [categories]
    logger.info(f"Creating {len(data)} glossary category asset(s)")
    logger.debug(f"Category specifications: {data}")

    specs = [GlossaryCategory(**item) for item in data]

    assets: List[AtlasGlossaryCategory] = []
    for spec in specs:
        logger.debug(f"Creating AtlasGlossaryCategory for: {spec.name}")
        anchor = AtlasGlossary.ref_by_guid(spec.glossary_guid)
        category = AtlasGlossaryCategory.creator(
            name=spec.name,
            anchor=anchor,
            parent_category=(
                AtlasGlossaryCategory.ref_by_guid(spec.parent_category_guid)
                if spec.parent_category_guid
                else None
            ),
        )
        category.user_description = spec.user_description
        if spec.certificate_status is not None:
            cs = (
                CertificateStatus(spec.certificate_status)
                if isinstance(spec.certificate_status, str)
                else spec.certificate_status
            )
            category.certificate_status = cs.value
            logger.debug(f"Set certificate status for {spec.name}: {cs.value}")
        if spec.parent_category_guid:
            logger.debug(
                f"Set parent category for {spec.name}: {spec.parent_category_guid}"
            )
        assets.append(category)

    return save_assets(assets)


def create_glossary_term_assets(
    terms: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Create one or multiple AtlasGlossaryTerm assets in Atlan.

    Args:
        terms (Union[Dict[str, Any], List[Dict[str, Any]]]): Either a single term
            specification (dict) or a list of term specifications. Each specification
            can be a dictionary containing:
            - name (str): Name of the term (required)
            - glossary_guid (str): GUID of the glossary this term belongs to (required)
            - user_description (str, optional): Detailed description of the term
              proposed by the user
            - certificate_status (str, optional): Certification status
              ("VERIFIED", "DRAFT", or "DEPRECATED")
            - categories (List[str], optional): List of category GUIDs this term
              belongs to

    Returns:
        Dict[str, Any]: Dictionary containing results list with details for each term
            creation attempt:
            - guid: The GUID of the created term (if successful)
            - name: The name of the term
            - qualified_name: The qualified name of the created term (if successful)
            - glossary_guid: The GUID of the parent glossary (if available)
            - category_guids: List of category GUIDs this term belongs to (if any)
            - success: Boolean indicating if creation was successful

    Raises:
        Exception: If there's an error creating the glossary term assets.
    """
    data = terms if isinstance(terms, list) else [terms]
    logger.info(f"Creating {len(data)} glossary term asset(s)")
    logger.debug(f"Term specifications: {data}")

    specs = [GlossaryTerm(**item) for item in data]

    assets: List[AtlasGlossaryTerm] = []
    for spec in specs:
        logger.debug(f"Creating AtlasGlossaryTerm for: {spec.name}")
        anchor = AtlasGlossary.ref_by_guid(spec.glossary_guid)
        category_refs = None
        if spec.categories:
            normalised_categories = parse_list_parameter(spec.categories)
            if normalised_categories:
                category_refs = [
                    AtlasGlossaryCategory.ref_by_guid(g) for g in normalised_categories
                ]
                logger.debug(f"Set categories for {spec.name}: {normalised_categories}")

        term = AtlasGlossaryTerm.creator(
            name=spec.name, anchor=anchor, categories=category_refs
        )
        term.user_description = spec.user_description
        if spec.certificate_status is not None:
            cs = (
                CertificateStatus(spec.certificate_status)
                if isinstance(spec.certificate_status, str)
                else spec.certificate_status
            )
            term.certificate_status = cs.value
            logger.debug(f"Set certificate status for {spec.name}: {cs.value}")
        assets.append(term)

    return save_assets(assets)

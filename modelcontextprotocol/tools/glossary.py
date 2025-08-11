from __future__ import annotations
import logging
from typing import Dict, Any, List, Union

from pyatlan.model.assets import (
    AtlasGlossary,
    AtlasGlossaryCategory,
    AtlasGlossaryTerm,
    Asset,
)
from pyatlan.model.fluent_search import FluentSearch
from utils.parameters import parse_list_parameter
from client import get_atlan_client
from .models import (
    CertificateStatus,
    Glossary,
    GlossaryCategory,
    GlossaryTerm,
)

logger = logging.getLogger(__name__)


def save_assets(assets: List[Asset]) -> List[Dict[str, Any]]:
    """
    Common bulk save and response processing for any asset type.

    Args:
        assets (List[Asset]): List of Asset objects to save.

    Returns:
        List[Dict[str, Any]]: List of dictionaries with details for each created asset.

    Raises:
        Exception: If there's an error saving the assets.
    """
    logger.info("Starting bulk save operation")
    client = get_atlan_client()
    try:
        response = client.asset.save(assets)
    except Exception as e:
        logger.error(f"Error saving assets: {e}")
        raise e
    results: List[Dict[str, Any]] = []
    created_assets = response.mutated_entities.CREATE

    logger.info(f"Save operation completed, processing {len(created_assets)} results")

    for created_asset in created_assets:
        results.append(
            {
                "guid": created_asset.guid,
                "name": created_asset.name,
                "qualified_name": created_asset.qualified_name,
            }
        )

    logger.info(f"Bulk save completed successfully for {len(results)} assets")
    return results


def create_glossary_assets(
    glossaries: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
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
        List[Dict[str, Any]]: List of dictionaries, each with details for a created glossary:
            - guid: The GUID of the created glossary
            - name: The name of the glossary
            - qualified_name: The qualified name of the created glossary

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
) -> List[Dict[str, Any]]:
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
        List[Dict[str, Any]]: List of dictionaries, each with details for a created category:
            - guid: The GUID of the created category
            - name: The name of the category
            - qualified_name: The qualified name of the created category

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

        assets.append(category)

    return save_assets(assets)


def create_glossary_term_assets(
    terms: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
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
            - category_guids (List[str], optional): List of category GUIDs this term
              belongs to

    Returns:
        List[Dict[str, Any]]: List of dictionaries, each with details for a created term:
            - guid: The GUID of the created term
            - name: The name of the term
            - qualified_name: The qualified name of the created term

    Raises:
        Exception: If there's an error creating the glossary term assets.
    """
    data = terms if isinstance(terms, list) else [terms]
    logger.info(f"Creating {len(data)} glossary term asset(s)")
    logger.debug(f"Term specifications: {data}")

    specs = [GlossaryTerm(**item) for item in data]
    # Collect and fetch category objects per term
    term_category_objects = []
    for spec in specs:
        category_guids = (
            parse_list_parameter(spec.category_guids) if spec.category_guids else []
        )

        if category_guids:
            try:
                search = (
                    FluentSearch()
                    .where(Asset.GUID.within(category_guids))
                    .where(Asset.TYPE_NAME.eq("AtlasGlossaryCategory"))
                )
                search_response = get_atlan_client().asset.search(search.to_request())
                term_category_objects.append(list(search_response.current_page()))
            except Exception as e:
                logger.warning(
                    f"Failed to fetch category objects for GUIDs {category_guids}: {e}"
                )
                term_category_objects.append([])
        else:
            term_category_objects.append([])

    assets: List[AtlasGlossaryTerm] = []
    for i, spec in enumerate(specs):
        logger.debug(f"Creating AtlasGlossaryTerm for: {spec.name}")
        anchor = AtlasGlossary.ref_by_guid(spec.glossary_guid)
        term = AtlasGlossaryTerm.creator(
            name=spec.name, anchor=anchor, categories=term_category_objects[i] or None
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

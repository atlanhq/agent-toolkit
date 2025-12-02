from __future__ import annotations
import logging
from typing import Dict, Any, List, Union

from pyatlan.model.assets import (
    AtlasGlossary,
    AtlasGlossaryCategory,
    AtlasGlossaryTerm,
)

from utils import parse_list_parameter, save_assets
from .models import (
    Glossary,
    GlossaryCategory,
    GlossaryTerm,
)

logger = logging.getLogger(__name__)


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
        if spec.certificate_status:
            glossary.certificate_status = spec.certificate_status.value
            logger.debug(
                f"Set certificate status for {spec.name}: {spec.certificate_status.value}"
            )
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
        if spec.certificate_status:
            category.certificate_status = spec.certificate_status.value
            logger.debug(
                f"Set certificate status for {spec.name}: {spec.certificate_status.value}"
            )

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
        ValueError: If any provided category_guids are not found.
        Exception: If there's an error creating the glossary term assets.
    """
    data = terms if isinstance(terms, list) else [terms]
    logger.info(f"Creating {len(data)} glossary term asset(s)")
    logger.debug(f"Term specifications: {data}")

    specs = [GlossaryTerm(**item) for item in data]
    per_term_guids = [set(parse_list_parameter(s.category_guids) or []) for s in specs]

    assets: List[AtlasGlossaryTerm] = []
    for spec, guids in zip(specs, per_term_guids):
        term = AtlasGlossaryTerm.creator(
            name=spec.name,
            anchor=AtlasGlossary.ref_by_guid(spec.glossary_guid),
            categories=[AtlasGlossaryCategory.ref_by_guid(g) for g in guids] or None,
        )
        term.user_description = spec.user_description
        if spec.certificate_status:
            term.certificate_status = spec.certificate_status.value
        assets.append(term)

    return save_assets(assets)

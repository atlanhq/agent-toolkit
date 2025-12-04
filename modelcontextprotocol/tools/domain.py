from __future__ import annotations

import logging
from typing import Any, Dict, List, Union

from pyatlan.model.assets import Asset, DataDomain, DataProduct
from pyatlan.model.fluent_search import CompoundQuery, FluentSearch

from utils import save_assets
from .models import DataDomainSpec, DataProductSpec

logger = logging.getLogger(__name__)


def create_data_domain_assets(
    domains: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Create one or multiple Data Domain or Sub Domain assets in Atlan.

    Args:
        domains (Union[Dict[str, Any], List[Dict[str, Any]]]): Either a single domain
            specification (dict) or a list of domain specifications. Each specification
            can be a dictionary containing:
            - name (str): Name of the domain (required)
            - parent_domain_qualified_name (str, optional): Qualified name of the parent
              domain. If provided, creates a Sub Domain under that parent.
            - user_description (str, optional): Detailed description of the domain
            - certificate_status (str, optional): Certification status
              ("VERIFIED", "DRAFT", or "DEPRECATED")

    Returns:
        List[Dict[str, Any]]: List of dictionaries, each with details for a created domain:
            - guid: The GUID of the created domain
            - name: The name of the domain
            - qualified_name: The qualified name of the created domain

    Raises:
        Exception: If there's an error creating the domain assets.
    """
    data = domains if isinstance(domains, list) else [domains]
    logger.info(f"Creating {len(data)} data domain asset(s)")
    logger.debug(f"Domain specifications: {data}")

    specs = [DataDomainSpec(**item) for item in data]

    assets: List[DataDomain] = []
    for spec in specs:
        logger.debug(
            f"Creating DataDomain: {spec.name}"
            + (
                f" under {spec.parent_domain_qualified_name}"
                if spec.parent_domain_qualified_name
                else ""
            )
        )
        domain = DataDomain.creator(
            name=spec.name,
            parent_domain_qualified_name=spec.parent_domain_qualified_name,
        )
        domain.user_description = spec.user_description
        domain.certificate_status = (
            spec.certificate_status.value if spec.certificate_status else None
        )

        if spec.certificate_status:
            logger.debug(
                f"Set certificate status for {spec.name}: {spec.certificate_status.value}"
            )

        assets.append(domain)

    return save_assets(assets)


def create_data_product_assets(
    products: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Create one or multiple Data Product assets in Atlan.

    Args:
        products (Union[Dict[str, Any], List[Dict[str, Any]]]): Either a single product
            specification (dict) or a list of product specifications. Each specification
            can be a dictionary containing:
            - name (str): Name of the product (required)
            - domain_qualified_name (str): Qualified name of the domain this product
              belongs to (required)
            - asset_guids (List[str]): List of asset GUIDs to link to this product
              (required, at least one)
            - user_description (str, optional): Detailed description of the product
            - certificate_status (str, optional): Certification status
              ("VERIFIED", "DRAFT", or "DEPRECATED")

    Returns:
        List[Dict[str, Any]]: List of dictionaries, each with details for a created product:
            - guid: The GUID of the created product
            - name: The name of the product
            - qualified_name: The qualified name of the created product

    Raises:
        Exception: If there's an error creating the product assets.
        ValueError: If no asset_guids are provided (validated in DataProductSpec model).
    """
    data = products if isinstance(products, list) else [products]
    logger.info(f"Creating {len(data)} data product asset(s)")
    logger.debug(f"Product specifications: {data}")

    # Validation for asset_guids is now handled by DataProductSpec model
    specs = [DataProductSpec(**item) for item in data]

    assets: List[DataProduct] = []
    for spec in specs:
        logger.debug(
            f"Creating DataProduct: {spec.name} under {spec.domain_qualified_name}"
        )
        logger.debug(f"Linking {len(spec.asset_guids)} asset(s) to product")

        # Build FluentSearch to select assets by their GUIDs
        asset_selection = (
            FluentSearch()
            .where(CompoundQuery.active_assets())
            .where(Asset.GUID.within(spec.asset_guids))
        ).to_request()

        product = DataProduct.creator(
            name=spec.name,
            domain_qualified_name=spec.domain_qualified_name,
            asset_selection=asset_selection,
        )
        product.user_description = spec.user_description
        product.certificate_status = (
            spec.certificate_status.value if spec.certificate_status else None
        )

        if spec.certificate_status:
            logger.debug(
                f"Set certificate status for {spec.name}: {spec.certificate_status.value}"
            )

        assets.append(product)

    return save_assets(assets)

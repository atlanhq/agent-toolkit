from __future__ import annotations
import logging
from typing import Dict, Any, List, Union

from pyatlan.model.assets import DataDomain, DataProduct, Asset
from pyatlan.model.search import IndexSearchRequest
from client import get_atlan_client
from .models import (
    CertificateStatus,
    DataDomainSpec,
    DataSubDomainSpec,
    DataProductSpec,
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

    results = [
        {
            "guid": created_asset.guid,
            "name": created_asset.name,
            "qualified_name": created_asset.qualified_name,
        }
        for created_asset in created_assets
    ]

    logger.info(f"Bulk save completed successfully for {len(results)} assets")
    return results


def create_data_domain_assets(
    domains: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Create one or multiple Data Domain assets in Atlan.

    Args:
        domains (Union[Dict[str, Any], List[Dict[str, Any]]]): Either a single domain
            specification (dict) or a list of domain specifications. Each specification
            can be a dictionary containing:
            - name (str): Name of the domain (required)
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
        logger.debug(f"Creating DataDomain for: {spec.name}")
        domain = DataDomain.creator(name=spec.name)
        domain.user_description = spec.user_description

        if spec.certificate_status is not None:
            cs = (
                CertificateStatus(spec.certificate_status)
                if isinstance(spec.certificate_status, str)
                else spec.certificate_status
            )
            domain.certificate_status = cs.value
            logger.debug(f"Set certificate status for {spec.name}: {cs.value}")

        assets.append(domain)

    return save_assets(assets)


def create_data_subdomain_assets(
    subdomains: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Create one or multiple Sub Domain (Data Domain with parent) assets in Atlan.

    Args:
        subdomains (Union[Dict[str, Any], List[Dict[str, Any]]]): Either a single subdomain
            specification (dict) or a list of subdomain specifications. Each specification
            can be a dictionary containing:
            - name (str): Name of the subdomain (required)
            - parent_domain_qualified_name (str): Qualified name of the parent domain (required)
            - user_description (str, optional): Detailed description of the subdomain
            - certificate_status (str, optional): Certification status
              ("VERIFIED", "DRAFT", or "DEPRECATED")

    Returns:
        List[Dict[str, Any]]: List of dictionaries, each with details for a created subdomain:
            - guid: The GUID of the created subdomain
            - name: The name of the subdomain
            - qualified_name: The qualified name of the created subdomain

    Raises:
        Exception: If there's an error creating the subdomain assets.
    """
    data = subdomains if isinstance(subdomains, list) else [subdomains]
    logger.info(f"Creating {len(data)} data subdomain asset(s)")
    logger.debug(f"Subdomain specifications: {data}")

    specs = [DataSubDomainSpec(**item) for item in data]

    assets: List[DataDomain] = []
    for spec in specs:
        logger.debug(
            f"Creating DataDomain (subdomain) for: {spec.name} under {spec.parent_domain_qualified_name}"
        )
        subdomain = DataDomain.creator(
            name=spec.name,
            parent_domain_qualified_name=spec.parent_domain_qualified_name,
        )
        subdomain.user_description = spec.user_description

        if spec.certificate_status is not None:
            cs = (
                CertificateStatus(spec.certificate_status)
                if isinstance(spec.certificate_status, str)
                else spec.certificate_status
            )
            subdomain.certificate_status = cs.value
            logger.debug(f"Set certificate status for {spec.name}: {cs.value}")

        assets.append(subdomain)

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
            - domain_qualified_name (str): Qualified name of the domain this product belongs to (required)
            - user_description (str, optional): Detailed description of the product
            - certificate_status (str, optional): Certification status
              ("VERIFIED", "DRAFT", or "DEPRECATED")
            - asset_selection (dict, optional): Asset selection query as a dictionary.
              This should be a FluentSearch request dictionary that defines which assets
              to link to the product.

    Returns:
        List[Dict[str, Any]]: List of dictionaries, each with details for a created product:
            - guid: The GUID of the created product
            - name: The name of the product
            - qualified_name: The qualified name of the created product

    Raises:
        Exception: If there's an error creating the product assets.
    """
    data = products if isinstance(products, list) else [products]
    logger.info(f"Creating {len(data)} data product asset(s)")
    logger.debug(f"Product specifications: {data}")

    specs = [DataProductSpec(**item) for item in data]

    assets: List[DataProduct] = []
    for spec in specs:
        logger.debug(
            f"Creating DataProduct for: {spec.name} under {spec.domain_qualified_name}"
        )

        # Handle asset selection if provided
        asset_selection = None
        if spec.asset_selection is not None:
            try:
                # Convert dict to IndexSearchRequest if needed
                asset_selection = IndexSearchRequest(**spec.asset_selection)
                logger.debug(f"Set asset selection for {spec.name}")
            except Exception as e:
                logger.warning(
                    f"Invalid asset_selection format for {spec.name}: {e}. Creating product without asset selection."
                )

        product = DataProduct.creator(
            name=spec.name,
            domain_qualified_name=spec.domain_qualified_name,
            asset_selection=asset_selection,
        )
        product.user_description = spec.user_description

        if spec.certificate_status is not None:
            cs = (
                CertificateStatus(spec.certificate_status)
                if isinstance(spec.certificate_status, str)
                else spec.certificate_status
            )
            product.certificate_status = cs.value
            logger.debug(f"Set certificate status for {spec.name}: {cs.value}")

        assets.append(product)

    return save_assets(assets)


def create_domain_assets(
    items: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Create Data Domains, Sub Domains, or Data Products based on the specification.

    This is a unified function that determines the type based on the presence of
    specific fields in the specification:
    - If 'parent_domain_qualified_name' is present -> Sub Domain
    - If 'domain_qualified_name' is present (and no parent) -> Data Product
    - Otherwise -> Data Domain

    Args:
        items (Union[Dict[str, Any], List[Dict[str, Any]]]): Either a single item
            specification (dict) or a list of item specifications. Each specification
            should contain fields appropriate for the type being created.

    Returns:
        List[Dict[str, Any]]: List of dictionaries, each with details for a created asset:
            - guid: The GUID of the created asset
            - name: The name of the asset
            - qualified_name: The qualified name of the created asset

    Raises:
        Exception: If there's an error creating the assets.
    """
    data = items if isinstance(items, list) else [items]
    logger.info(f"Creating {len(data)} domain-related asset(s)")

    # Separate items by type
    domains = []
    subdomains = []
    products = []

    for item in data:
        if "parent_domain_qualified_name" in item:
            subdomains.append(item)
        elif "domain_qualified_name" in item:
            products.append(item)
        else:
            domains.append(item)

    results = []

    # Create domains
    if domains:
        logger.info(f"Creating {len(domains)} data domain(s)")
        results.extend(create_data_domain_assets(domains))

    # Create subdomains
    if subdomains:
        logger.info(f"Creating {len(subdomains)} data subdomain(s)")
        results.extend(create_data_subdomain_assets(subdomains))

    # Create products
    if products:
        logger.info(f"Creating {len(products)} data product(s)")
        results.extend(create_data_product_assets(products))

    return results

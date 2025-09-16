"""
Data domain management tools for Atlan MCP server.

This module provides functions to retrieve Atlan data domains.
"""

import logging
from typing import Dict, Any, Optional
from client import get_atlan_client
from pyatlan.model.assets import DataDomain
from pyatlan.model.assets import Asset

logger = logging.getLogger(__name__)

# Constants
DEFAULT_SEARCH_SIZE = 1  # Expected number of domains in search results


def _extract_relationship_attributes(value, atlan_client, is_list=True):
    """
    Helper function to extract relationship attributes with full details.

    Args:
        value: The relationship value (single object or list)
        atlan_client: Atlan client for API calls
        is_list: Whether to expect a list or single object

    Returns:
        List of relationship objects with full details or single object
    """
    if value is None:
        return [] if is_list else None

    items = value if isinstance(value, list) else [value]
    relationship_objects = []

    for item in items:
        item_guid = getattr(item, "guid", None)
        item_name = getattr(item, "name", None)
        item_qualified_name = getattr(item, "qualified_name", None)
        full_asset = None

        # If name is missing, try to fetch full details using GUID
        if item_name is None and item_guid:
            try:
                logger.debug(
                    f"Fetching full details for relationship asset: {item_guid}"
                )
                full_asset = atlan_client.asset.get_by_guid(guid=item_guid)
                if full_asset:
                    item_name = getattr(full_asset, "name", None) or getattr(
                        full_asset, "display_name", None
                    )
                    if not item_qualified_name:
                        item_qualified_name = getattr(
                            full_asset, "qualified_name", None
                        )
                    logger.debug(f"Retrieved name: {item_name}")
            except Exception as e:
                logger.debug(f"Failed to fetch full details for {item_guid}: {e}")

        # Use hybrid approach: get all attributes from the relationship object
        source_obj = full_asset if full_asset else item

        # Start with the relationship object's attributes using dict() if available
        if hasattr(source_obj, "dict"):
            try:
                relationship_obj = source_obj.dict(exclude_none=True)

                # Flatten nested attributes field (same as main domain logic)
                if "attributes" in relationship_obj and isinstance(
                    relationship_obj["attributes"], dict
                ):
                    nested_attrs = relationship_obj.pop(
                        "attributes"
                    )  # Remove and extract
                    # Add nested attributes to top level
                    relationship_obj.update(nested_attrs)

            except Exception:
                # Fall back to manual attribute extraction if dict() fails
                relationship_obj = {
                    "guid": item_guid,
                    "type_name": getattr(source_obj, "type_name", None),
                    "qualified_name": item_qualified_name,
                    "name": item_name,
                    "display_name": getattr(source_obj, "display_name", None),
                    "description": getattr(source_obj, "description", None),
                    "status": getattr(source_obj, "status", None),
                    "created_by": getattr(source_obj, "created_by", None),
                    "updated_by": getattr(source_obj, "updated_by", None),
                    "create_time": getattr(source_obj, "create_time", None),
                    "update_time": getattr(source_obj, "update_time", None),
                }
        else:
            # Manual extraction for objects without dict() method
            relationship_obj = {
                "guid": item_guid,
                "type_name": getattr(source_obj, "type_name", None),
                "qualified_name": item_qualified_name,
                "name": item_name,
                "display_name": getattr(source_obj, "display_name", None),
                "description": getattr(source_obj, "description", None),
                "status": getattr(source_obj, "status", None),
                "created_by": getattr(source_obj, "created_by", None),
                "updated_by": getattr(source_obj, "updated_by", None),
                "create_time": getattr(source_obj, "create_time", None),
                "update_time": getattr(source_obj, "update_time", None),
            }

        relationship_objects.append(relationship_obj)

    return (
        relationship_objects
        if is_list
        else (relationship_objects[0] if relationship_objects else None)
    )


def retrieve_domain(
    guid: Optional[str] = None, qualified_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve a specific data domain by GUID or qualified name.

    Args:
        guid (str, optional): GUID of the data domain to retrieve.
        qualified_name (str, optional): Qualified name of the data domain to retrieve.
            Format typically: "default/domain/{domain-name}"

    Note:
        Exactly one of guid or qualified_name must be provided.

    Returns:
        Dict[str, Any]: Dictionary containing domain details or error information.
            - domain: Data domain object with all relevant attributes including:
                - Basic attributes: guid, qualified_name, name, display_name, description, etc.
                - Metadata: created_by, updated_by, create_time, update_time, status, etc.
                - Domain hierarchy: parent_domain (single object), sub_domains (list of objects)
                - Relationships: stakeholders (list of objects)
                - Domain-specific: parent_domain_qualified_name, super_domain_qualified_name
            - error: None if successful, error message otherwise

    Note:
        Relationship objects (sub_domains, parent_domain, stakeholders) include full details
        with all relevant attributes extracted via additional API calls when necessary.

    Examples:
        # Retrieve a data domain by qualified name
        domain = retrieve_domain(qualified_name="default/domain/marketing")

        # Retrieve a subdomain
        subdomain = retrieve_domain(qualified_name="default/domain/marketing/campaigns")

        # Retrieve by GUID
        domain = retrieve_domain(guid="12345678-1234-1234-1234-123456789abc")
    """
    # Validate input parameters
    if not guid and not qualified_name:
        return {
            "domain": None,
            "error": "Either 'guid' or 'qualified_name' must be provided",
        }

    if guid and qualified_name:
        return {
            "domain": None,
            "error": "Only one of 'guid' or 'qualified_name' should be provided, not both",
        }

    identifier = guid if guid else qualified_name
    lookup_type = "GUID" if guid else "qualified name"
    logger.info(f"Retrieving data domain by {lookup_type}: {identifier}")

    try:
        atlan_client = get_atlan_client()

        # Use FluentSearch to get domain with all attributes (hybrid approach simplification)
        from pyatlan.model.fluent_search import FluentSearch, CompoundQuery

        search = FluentSearch()
        search = search.where(CompoundQuery.asset_type(DataDomain))

        if guid:
            logger.debug(f"Searching for domain by GUID: {guid}")
            search = search.where(Asset.GUID.eq(guid))
        else:
            logger.debug(f"Searching for domain by qualified name: {qualified_name}")
            search = search.where(Asset.QUALIFIED_NAME.eq(qualified_name))

        # Include key relationship attributes in search (domain.dict() will get the rest)
        search = search.include_on_results(DataDomain.SUB_DOMAINS)
        search = search.include_on_results(DataDomain.PARENT_DOMAIN)
        search = search.include_on_results(DataDomain.STAKEHOLDERS)

        # Include basic attributes on relationships for enrichment
        search = search.include_on_relations(Asset.NAME)
        search = search.include_on_relations(Asset.QUALIFIED_NAME)
        search = search.include_on_relations(Asset.DESCRIPTION)

        # Execute search
        request = search.to_request()
        request.size = DEFAULT_SEARCH_SIZE

        logger.debug("Executing simplified domain search request")
        response = atlan_client.asset.search(request)

        # Get the first result
        domain = None
        for asset in response.current_page():
            domain = asset
            break

        if domain:
            # Use hybrid approach: domain.dict() for base attributes + relationship attributes
            logger.debug(
                "Using hybrid approach: domain.dict() + relationship attributes"
            )

            # Start with all base attributes from Pydantic serialization (excludes None values for cleaner output)
            domain_dict = domain.dict(exclude_none=True)

            # Flatten nested attributes field (PyAtlan stores business attributes here)
            if "attributes" in domain_dict and isinstance(
                domain_dict["attributes"], dict
            ):
                nested_attrs = domain_dict.pop("attributes")  # Remove and extract
                # Add nested attributes to top level (these are the main business attributes)
                domain_dict.update(nested_attrs)
                logger.debug(
                    f"Flattened {len(nested_attrs)} business attributes from nested structure"
                )

            # Add relationship attributes manually (these are not included in domain.dict())
            relationship_attributes = {
                "sub_domains": getattr(domain, "sub_domains", None),
                "parent_domain": getattr(domain, "parent_domain", None),
                "stakeholders": getattr(domain, "stakeholders", None),
            }

            # Add relationship attributes and apply enrichment
            for attr_name, attr_value in relationship_attributes.items():
                if attr_value is not None:
                    # Apply relationship enrichment using helper function
                    if attr_name == "sub_domains":
                        domain_dict[attr_name] = _extract_relationship_attributes(
                            attr_value, atlan_client, is_list=True
                        )
                    elif attr_name == "parent_domain":
                        domain_dict[attr_name] = _extract_relationship_attributes(
                            attr_value, atlan_client, is_list=False
                        )
                    elif attr_name == "stakeholders":
                        domain_dict[attr_name] = _extract_relationship_attributes(
                            attr_value, atlan_client, is_list=True
                        )
                else:
                    # Include None values for consistency
                    domain_dict[attr_name] = None

            logger.debug(
                f"Retrieved domain with {len(domain_dict)} attributes (hybrid approach with flattening)"
            )

            logger.info(f"Successfully retrieved data domain: {domain.name}")
            return {"domain": domain_dict, "error": None}
        else:
            raise Exception(f"Data domain not found with {lookup_type}: {identifier}")

    except Exception as e:
        logger.error(f"Error retrieving data domain: {str(e)}")
        logger.exception("Exception details:")
        return {
            "domain": None,
            "error": str(e),
        }

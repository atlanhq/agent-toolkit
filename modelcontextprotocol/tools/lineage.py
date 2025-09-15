import logging
from typing import Dict, Any, List, Optional, Union

from client import get_atlan_client
from pyatlan.model.enums import LineageDirection
from pyatlan.model.lineage import FluentLineage
from pyatlan.model.fields.atlan_fields import AtlanField
from utils.search import SearchUtils
from utils.constants import DEFAULT_SEARCH_ATTRIBUTES

# Configure logging
logger = logging.getLogger(__name__)


def traverse_lineage(
    guid: str,
    direction: LineageDirection,
    depth: int = 1000000,
    size: int = 10,
    immediate_neighbors: bool = False,
    include_attributes: Optional[List[Union[str, AtlanField]]] = None,
) -> Dict[str, Any]:
    """
    Traverse asset lineage in specified direction.

    By default, essential attributes used in search operations are included.
    Additional attributes can be specified via include_attributes parameter.

    Args:
        guid (str): GUID of the starting asset
        direction (LineageDirection): Direction to traverse (UPSTREAM or DOWNSTREAM)
        depth (int, optional): Maximum depth to traverse. Defaults to 1000000.
        size (int, optional): Maximum number of results to return. Defaults to 10.
        immediate_neighbors (bool, optional): Only return immediate neighbors. Defaults to False.
        include_attributes (Optional[List[Union[str, AtlanField]]], optional): List of additional
            attributes to include in results. Can be string attribute names or AtlanField objects.
            These will be added to the default set. Defaults to None.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - assets: List of assets in the lineage with processed attributes
            - error: None if no error occurred, otherwise the error message

    Raises:
        Exception: If there's an error executing the lineage request
    """
    logger.info(
        f"Starting lineage traversal from {guid} in direction {direction}, "
        f"depth={depth}, size={size}, immediate_neighbors={immediate_neighbors}"
    )
    logger.debug(f"Include attributes parameter: {include_attributes}")

    try:
        # Initialize base request
        logger.debug("Initializing FluentLineage object")
        lineage_builder = (
            FluentLineage(starting_guid=guid)
            .direction(direction)
            .depth(depth)
            .size(size)
            .immediate_neighbors(immediate_neighbors)
        )

        # Prepare attributes to include: default attributes + additional user-specified attributes
        all_attributes = DEFAULT_SEARCH_ATTRIBUTES.copy()

        if include_attributes:
            logger.debug(f"Adding user-specified attributes: {include_attributes}")
            for attr in include_attributes:
                if isinstance(attr, str) and attr not in all_attributes:
                    all_attributes.append(attr)

        logger.debug(f"Total attributes to include: {all_attributes}")

        # Include all string attributes in results
        for attr_name in all_attributes:
            attr_obj = SearchUtils._get_asset_attribute(attr_name)
            if attr_obj is None:
                logger.warning(
                    f"Unknown attribute for inclusion: {attr_name}, skipping"
                )
                continue
            logger.debug(f"Including attribute: {attr_name}")
            lineage_builder = lineage_builder.include_on_results(attr_obj)

        # Execute request
        logger.debug("Converting FluentLineage to request object")
        request = lineage_builder.request

        logger.info("Executing lineage request")
        client = get_atlan_client()
        response = client.asset.get_lineage_list(request)

        # Process results using same pattern as search
        logger.info("Processing lineage results")
        if response is None:
            logger.info("No lineage results found")
            return {"assets": [], "error": None}

        # Convert results to list and process using Pydantic serialization
        results_list = [
            result.dict(by_alias=True, exclude_unset=True)
            for result in response
            if result is not None
        ]

        logger.info(
            f"Lineage traversal completed, returned {len(results_list)} results"
        )
        return {"assets": results_list, "error": None}

    except Exception as e:
        logger.error(f"Error traversing lineage: {str(e)}")
        return {"assets": [], "error": str(e)}

def get_asset_source_or_destination(
    guid: str,
    direction: LineageDirection,
    depth: int = 1000000,
    size: int = 100,
    ignore_types: Optional[List[str]] = ['process', 'aimodel']
) -> Dict[str, Any]:
    """
    Get the source or destination assets for a given asset by traversing lineage.

    This function identifies terminal assets in the lineage graph - either source assets
    (those with no upstream dependencies) or destination assets (those with no downstream
    dependencies). Asset types can be filtered out using the ignore_types parameter.

    Args:
        guid (str): GUID of the starting asset
        direction (LineageDirection): Direction to traverse (UPSTREAM for sources, DOWNSTREAM for destinations)
        depth (int, optional): Maximum depth to traverse. Defaults to 1000000.
        size (int, optional): Maximum number of results to return. Defaults to 100.
        ignore_types (Optional[List[str]], optional): List of asset type keywords to ignore
            (case-insensitive matching). Defaults to ['process', 'aimodel'].

    Returns:
        Dict[str, Any]: Dictionary containing:
            - assets: List of terminal assets (sources or destinations) with processed attributes
            - error: None if no error occurred, otherwise the error message

    Raises:
        ValueError: If direction is not UPSTREAM or DOWNSTREAM
        Exception: If there's an error executing the lineage request
    """
    
    logger.info(f"Starting lineage source check for {guid}, depth={depth}, size={size}")
    logger.info(f"Ignore types: {ignore_types}")

    try:
        client = get_atlan_client()
        request = (
            FluentLineage(starting_guid=guid)
            .direction(direction)
            .immediate_neighbors(True)
            .depth(depth)
            .size(size)
            .request
        )
        response = client.asset.get_lineage_list(request)
        assets = []
        for asset in response:
            if direction == LineageDirection.UPSTREAM: # This is a source check
                # Check if the asset has the 'immediate_upstream' attribute and if it's not empty
                if not hasattr(asset, 'immediate_upstream') or not asset.immediate_upstream:
                    # Skip assets that contain any of the exclude keywords in their type_name
                    if hasattr(asset, 'type_name'):
                        asset_type = asset.type_name.lower()
                        if any(keyword in asset_type for keyword in ignore_types):
                            continue  # Skip assets with excluded keywords
                    assets.append(asset.dict(by_alias=True, exclude_unset=True))
                logger.info(f"Total assets with no immediate {direction} lineage: {len(assets)}")
            elif direction == LineageDirection.DOWNSTREAM: # This is a destination check
                # Check to make sure it's not the same asset
                if asset.guid == guid:
                    continue
                # Check if the asset has the 'immediate_downstream' attribute and if it's not empty
                if not hasattr(asset, 'immediate_downstream') or not asset.immediate_downstream:
                    # Skip assets that contain any of the exclude keywords in their type_name
                    if hasattr(asset, 'type_name'):
                        asset_type = asset.type_name.lower()
                        if any(keyword in asset_type for keyword in ignore_types):
                            continue  # Skip assets with excluded keywords
                    assets.append(asset.dict(by_alias=True, exclude_unset=True))
                logger.info(f"Total assets with no immediate {direction} lineage: {len(assets)}")
            else:
                raise ValueError(f"Invalid direction: {direction}. Must be either 'UPSTREAM' or 'DOWNSTREAM'")
        return {"assets": assets, "error": None}
    except Exception as e:
        logger.error(f"Error traversing lineage source or destination: {str(e)}")
        return {"assets": [], "error": str(e)}
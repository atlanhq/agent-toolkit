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

import logging
from typing import Dict, Any

from client import get_atlan_client
from pyatlan.model.enums import LineageDirection
from pyatlan.model.lineage import FluentLineage

# Configure logging
logger = logging.getLogger(__name__)


def traverse_lineage(
    guid: str,
    direction: LineageDirection,
    depth: int = 1000000,
    size: int = 10,
    immediate_neighbors: bool = False,
) -> Dict[str, Any]:
    """
    Traverse asset lineage in specified direction.

    Args:
        guid (str): GUID of the starting asset
        direction (LineageDirection): Direction to traverse (UPSTREAM or DOWNSTREAM)
        depth (int, optional): Maximum depth to traverse. Defaults to 1000000.
        size (int, optional): Maximum number of results to return. Defaults to 10.
        immediate_neighbors (bool, optional): Only return immediate neighbors. Defaults to True.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - assets: List of assets in the lineage
            - references: List of dictionaries containing:
                - source_guid: GUID of the source asset
                - target_guid: GUID of the target asset
                - direction: Direction of the reference (upstream/downstream)

    Raises:
        Exception: If there's an error executing the lineage request
    """
    logger.info(f"Starting lineage traversal from {guid} in direction {direction}")

    try:
        # Initialize base request
        request = (
            FluentLineage(starting_guid=guid)
            .direction(direction)
            .depth(depth)
            .size(size)
            .immediate_neighbors(immediate_neighbors)
            .request
        )

        # Execute request
        logger.debug("Executing lineage request")
        client = get_atlan_client()
        response = client.asset.get_lineage_list(request)  # noqa: F821

        # Process results
        result = {"assets": []}

        # Handle None response
        if response is None:
            logger.info("No lineage results found")
            return result

        assets = []
        for item in response:
            if item is None:
                continue
            assets.append(item)
        result["assets"] = assets
        return result
    except Exception as e:
        logger.error(f"Error traversing lineage: {str(e)}")
        return {"assets": [], "error": str(e)}

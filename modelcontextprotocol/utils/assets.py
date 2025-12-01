"""
Asset utilities for the Atlan MCP server.

This module provides reusable functions for asset operations
that are commonly used across different MCP tools.
"""

import logging
from typing import Any, Dict, List

from pyatlan.model.assets import Asset

from client import get_atlan_client

logger = logging.getLogger(__name__)


def save_assets(assets: List[Asset]) -> List[Dict[str, Any]]:
    """
    Common bulk save and response processing for any asset type.

    Args:
        assets (List[Asset]): List of Asset objects to save.

    Returns:
        List[Dict[str, Any]]: List of dictionaries with details for each created
            or updated asset.

    Raises:
        Exception: If there's an error saving the assets.
    """
    logger.info("Starting bulk save operation")
    client = get_atlan_client()
    try:
        response = client.asset.save(assets)
    except Exception as e:
        logger.error(f"Error saving assets: {e}")
        raise

    created_assets = response.mutated_entities.CREATE or []
    updated_assets = response.mutated_entities.UPDATE or []

    logger.info(
        f"Save operation completed: {len(created_assets)} created, "
        f"{len(updated_assets)} updated"
    )

    results = []

    # Process created assets
    for asset in created_assets:
        results.append(
            {
                "guid": asset.guid,
                "name": asset.name,
                "qualified_name": asset.qualified_name,
                "operation": "CREATE",
            }
        )

    # Process updated assets
    for asset in updated_assets:
        results.append(
            {
                "guid": asset.guid,
                "name": asset.name,
                "qualified_name": asset.qualified_name,
                "operation": "UPDATE",
            }
        )

    logger.info(f"Bulk save completed successfully for {len(results)} assets")
    return results

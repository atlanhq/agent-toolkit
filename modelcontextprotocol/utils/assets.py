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
        raise

    created_assets = response.mutated_entities.CREATE
    logger.info(f"Save operation completed, processing {len(created_assets)} results")

    results = [
        {
            "guid": asset.guid,
            "name": asset.name,
            "qualified_name": asset.qualified_name,
        }
        for asset in created_assets
    ]

    logger.info(f"Bulk save completed successfully for {len(results)} assets")
    return results

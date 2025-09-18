"""Header utilities for Atlan MCP tools."""

import logging
from client import get_atlan_client
from settings import get_settings

logger = logging.getLogger(__name__)


def set_tool_headers(tool_name: str) -> None:
    """Set tool-specific headers for the Atlan client."""
    try:
        settings = get_settings()
        get_atlan_client().update_headers({settings.ATLAN_PACKAGE_NAME: tool_name})
    except Exception as e:
        logger.warning(f"Could not set headers for {tool_name}: {e}")



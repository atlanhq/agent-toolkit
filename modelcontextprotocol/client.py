"""Client factory for Atlan."""

import logging
from typing import Optional
from contextvars import ContextVar

from pyatlan.client.atlan import AtlanClient
from settings import Settings

logger = logging.getLogger(__name__)

_client_instance: Optional[AtlanClient] = None
current_tool_name: ContextVar[str] = ContextVar("current_tool_name", default=None)


def get_atlan_client() -> AtlanClient:
    """
    Get the singleton AtlanClient instance for connection reuse.

    Returns:
        AtlanClient: The singleton AtlanClient instance.

    Raises:
        Exception: If client creation fails.
    """
    global _client_instance

    if _client_instance is None:
        settings = Settings()
        try:
            _client_instance = AtlanClient(
                base_url=settings.ATLAN_BASE_URL, api_key=settings.ATLAN_API_KEY
            )
            _client_instance.update_headers(settings.headers)
            logger.info("AtlanClient initialized successfully")
        except Exception:
            logger.error("Failed to create Atlan client", exc_info=True)
            raise

    # Always update headers with current tool name if available
    settings = Settings()
    headers = settings.headers.copy()
    tool_name = current_tool_name.get()
    if tool_name:
        headers["x-atlan-package-name"] = tool_name
        logger.debug(f"Added x-atlan-package-name header: {tool_name}")
        _client_instance.update_headers(headers)

    return _client_instance

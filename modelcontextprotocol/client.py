"""Client factory for Atlan."""

import logging
from typing import Optional

from pyatlan.client.atlan import AtlanClient
from settings import Settings

logger = logging.getLogger(__name__)

# Lazy initialization of client
_atlan_client: Optional[AtlanClient] = None


def get_atlan_client() -> AtlanClient:
    """Get the Atlan client instance, initializing it if needed."""
    global _atlan_client
    if _atlan_client is None:
        _atlan_client = create_atlan_client()
    return _atlan_client


def create_atlan_client() -> AtlanClient:
    """Create an Atlan client instance using settings loaded from environment."""
    settings = Settings()

    missing_vars = []
    if not settings.atlan_base_url:
        missing_vars.append("ATLAN_BASE_URL")
    if not settings.atlan_api_key:
        missing_vars.append("ATLAN_API_KEY")
    if not settings.atlan_agent_id:
        missing_vars.append("ATLAN_AGENT_ID")

    if missing_vars:
        error_msg = (
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            f"Please add them to your .env file or set them in your environment."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        client = AtlanClient(
            base_url=settings.atlan_base_url, api_key=settings.atlan_api_key
        )
        client.update_headers(settings.headers)
        logger.info("Atlan client created successfully")
        return client
    except Exception as e:
        logger.error(f"Error creating Atlan client: {e}")
        raise Exception(f"Error creating Atlan client: {e}")

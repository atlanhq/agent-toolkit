"""Client factory for Atlan."""

import logging

from pyatlan.client.atlan import AtlanClient
from settings import Settings

logger = logging.getLogger(__name__)


def get_atlan_client() -> AtlanClient:
    """Create an Atlan client instance using settings loaded from environment."""
    settings = Settings()

    try:
        client = AtlanClient(
            base_url=settings.ATLAN_BASE_URL, api_key=settings.ATLAN_API_KEY
        )
        client.update_headers(settings.headers)
        logger.info("Atlan client created successfully")
        return client
    except Exception as e:
        logger.error(f"Error creating Atlan client: {e}")
        raise Exception(f"Error creating Atlan client: {e}")

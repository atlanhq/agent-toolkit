"""Client factory for Atlan."""

import logging

from pyatlan.client.atlan import AtlanClient

from settings import Settings

logger = logging.getLogger(__name__)


def create_atlan_client(settings: Settings) -> AtlanClient:
    """Create an Atlan client instance using the provided settings.

    Args:
        settings: Application settings containing Atlan credentials

    Returns:
        An initialized AtlanClient instance
    """
    try:
        client = AtlanClient(
            base_url=settings.atlan_base_url, api_key=settings.atlan_api_key
        )
        logger.info("Atlan client created successfully")
        return client
    except Exception as e:
        logger.error(f"Error creating Atlan client: {e}")
        raise e

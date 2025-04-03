"""Client factory for Atlan."""

from config import Settings
from pyatlan.client.atlan import AtlanClient


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
        return client
    except Exception as e:
        raise e

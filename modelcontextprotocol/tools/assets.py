import logging
from typing import List, Union, Dict, Any

from client import get_atlan_client
from .models import UpdatableAsset, UpdatableAttribute, CertificateStatus

# Configure logging
logger = logging.getLogger(__name__)


def update_assets(
    updatable_assets: Union[UpdatableAsset, List[UpdatableAsset]],
    attribute_name: UpdatableAttribute,
    attribute_values: List[Union[str, CertificateStatus]],
) -> Dict[str, Any]:
    """
    Update one or multiple assets with different values for the same attribute.

    Args:
        updatable_assets (Union[UpdatableAsset, List[UpdatableAsset]]): Asset(s) to update.
            Can be a single UpdatableAsset or a list of UpdatableAssets.
        attribute_name (UpdatableAttribute): Name of the attribute to update.
            Only userDescription and certificateStatus are allowed.
        attribute_values (List[Union[str, CertificateStatus]]): List of values to set for the attribute.
            For certificateStatus, only VERIFIED, DRAFT, or DEPRECATED are allowed.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - updated_count: Number of assets successfully updated
            - errors: List of any errors encountered
    """
    try:
        # Convert single GUID to list for consistent handling
        if not isinstance(updatable_assets, list):
            updatable_assets = [updatable_assets]

        logger.info(
            f"Updating {len(updatable_assets)} assets with attribute '{attribute_name}'"
        )

        # Validate attribute values
        if len(updatable_assets) != len(attribute_values):
            error_msg = "Number of asset GUIDs must match number of attribute values"
            logger.error(error_msg)
            return {"updated_count": 0, "errors": [error_msg]}

        # Initialize result tracking
        result = {"updated_count": 0, "errors": []}

        # Validate certificate status values if applicable
        if attribute_name == UpdatableAttribute.CERTIFICATE_STATUS:
            for value in attribute_values:
                if value not in CertificateStatus.__members__.values():
                    error_msg = f"Invalid certificate status: {value}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)

        # Get Atlan client
        client = get_atlan_client()

        # Create assets with updated values
        assets = []
        index = 0
        for updatable_asset in updatable_assets:
            type_name = updatable_asset.type_name
            asset_cls = getattr(
                __import__("pyatlan.model.assets", fromlist=[type_name]), type_name
            )
            asset = asset_cls.updater(
                qualified_name=updatable_asset.qualified_name,
                name=updatable_asset.name,
            )
            setattr(asset, attribute_name.value, attribute_values[index])
            assets.append(asset)
            index += 1
        response = client.asset.save(assets)

        # Process response
        result["updated_count"] = len(response.guid_assignments)
        logger.info(f"Successfully updated {result['updated_count']} assets")
        return result

    except Exception as e:
        error_msg = f"Error updating assets: {str(e)}"
        logger.error(error_msg)
        return {"updated_count": 0, "errors": [error_msg]}

import html5lib
import logging
from typing import List, Union, Dict, Any
from client import get_atlan_client
from .models import UpdatableAsset, UpdatableAttribute, CertificateStatus
from pyatlan.model.assets import Readme
from pyatlan.model.fluent_search import CompoundQuery, FluentSearch

# Initialize logging
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
            Only userDescription,certificateStatus and readme are allowed.
        attribute_values (List[Union[str, CertificateStatus]]): List of values to set for the attribute.
            For certificateStatus, only VERIFIED, DRAFT, or DEPRECATED are allowed.
            For readme, the value must be a valid HTML string without <html> and <body> tags.

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

        if attribute_name == UpdatableAttribute.README:
            for value in attribute_values:
                if not isinstance(value, str):
                    error_msg = f"Invalid readme: {value}. Must be a string."
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                else:
                    # Readme in Atlan is rendered as HTML
                    # Wrap the value in HTML tags to make it a valid HTML string
                    wrapped_value = f"<html><body>{value}</body></html>"
                    try:
                        html5lib.parse(wrapped_value)
                    except Exception:
                        error_msg = f"Invalid readme: {value}. Must be a valid HTML string without <html> and <body> tags."
                        logger.error(error_msg)
                        result["errors"].append(error_msg)

        # Get Atlan client
        client = get_atlan_client()

        # Create assets with updated values
        assets = []
        # Maintain separate lists for readme updates to avoid confusion with other asset attribute updates.
        # readme_update_assets: Readme assets to update.
        # readme_update_parent_assets: Assets that were updated with readme.
        readme_update_assets = []
        readme_update_parent_assets = []
        index = 0
        for updatable_asset in updatable_assets:
            type_name = updatable_asset.type_name
            qualified_name = updatable_asset.qualified_name
            asset_cls = getattr(
                __import__("pyatlan.model.assets", fromlist=[type_name]), type_name
            )
            asset = asset_cls.updater(
                    qualified_name=updatable_asset.qualified_name,
                    name=updatable_asset.name,
                )
            
            # Special handling for README updates
            if attribute_name == UpdatableAttribute.README:
                response_readme_fetch = (
                    FluentSearch()
                    .select()
                    .where(CompoundQuery.asset_type(asset_cls))
                    .where(asset_cls.QUALIFIED_NAME.eq(qualified_name))
                    .include_on_results(asset_cls.README)
                    .include_on_relations(Readme.DESCRIPTION)
                    .execute(client=client)
                )

                if first := response_readme_fetch.current_page():
                    updated_content = attribute_values[index]
                    updated_readme = Readme.creator(
                        asset=first[0], content=updated_content
                    )
                    # Save the readme asset
                    # Readme asset is created in the same request as the parent asset.
                    readme_update_assets.append(updated_readme)
                    # Add the parent/actual asset to the list of assets that were updated with readme.
                    readme_update_parent_assets.append(asset)
            else:
                # Regular attribute update flow
                setattr(asset, attribute_name.value, attribute_values[index])
                assets.append(asset)

            index += 1

        if len(readme_update_assets) > 0:
            readme_update_response = client.asset.save(readme_update_assets)
            updated_guids = list(readme_update_response.guid_assignments.keys())
            result["readme_updated"] = len(updated_guids)
            # Collect qualified names or other identifiers for assets that were updated with readme
            result["updated_readme_assets"] = [
                asset.qualified_name for asset in readme_update_parent_assets
                if hasattr(asset, "qualified_name")
            ]
            logger.info(f"Successfully updated {result['readme_updated']} readme assets: {result['updated_readme_assets']}")

        if len(assets) > 0:
            response = client.asset.save(assets)
            result["updated_count"] = len(response.guid_assignments)
            logger.info(f"Successfully updated {result['updated_count']} assets")

        return result

    except Exception as e:
        error_msg = f"Error updating assets: {str(e)}"
        logger.error(error_msg)
        return {"updated_count": 0, "errors": [error_msg]}

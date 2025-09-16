import logging
from typing import List, Union, Dict, Any, Optional
from client import get_atlan_client
from .models import UpdatableAsset, UpdatableAttribute, CertificateStatus
from pyatlan.model.assets import Readme
from pyatlan.model.fluent_search import CompoundQuery, FluentSearch
from pyatlan.model.fields.atlan_fields import AtlanField
from utils.asset_history import (
    validate_asset_history_params,
    create_audit_search_request,
    process_audit_result,
    create_sort_item,
    convert_attributes_to_camel_case,
)

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
            For readme, the value must be a valid Markdown string.

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
        # readme_update_parent_assets: Assets that were updated with readme.
        readme_update_parent_assets = []
        for index, updatable_asset in enumerate(updatable_assets):
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
                # Get the current readme content for the asset
                # The below query is used to get the asset based on the qualified name and include the readme content.
                asset_readme_response = (
                    FluentSearch()
                    .select()
                    .where(CompoundQuery.asset_type(asset_cls))
                    .where(asset_cls.QUALIFIED_NAME.eq(qualified_name))
                    .include_on_results(asset_cls.README)
                    .include_on_relations(Readme.DESCRIPTION)
                    .execute(client=client)
                )

                if first := asset_readme_response.current_page():
                    updated_content = attribute_values[index]
                    # We replace the existing readme content with the new content.
                    # If the existing readme content is not present, we create a new readme asset.
                    updated_readme = Readme.creator(
                        asset=first[0], content=updated_content
                    )
                    # Save the readme asset
                    assets.append(updated_readme)
                    # Add the parent/actual asset to the list of assets that were updated with readme.
                    readme_update_parent_assets.append(asset)
            else:
                # Regular attribute update flow
                setattr(asset, attribute_name.value, attribute_values[index])
                assets.append(asset)

        if len(readme_update_parent_assets) > 0:
            result["readme_updated"] = len(readme_update_parent_assets)
            # Collect qualified names or other identifiers for assets that were updated with readme
            result["updated_readme_assets"] = [
                asset.qualified_name
                for asset in readme_update_parent_assets
                if hasattr(asset, "qualified_name")
            ]
            logger.info(
                f"Successfully updated {result['readme_updated']} readme assets: {result['updated_readme_assets']}"
            )

        # Proces response
        response = client.asset.save(assets)
        result["updated_count"] = len(response.guid_assignments)
        logger.info(f"Successfully updated {result['updated_count']} assets")

        return result

    except Exception as e:
        error_msg = f"Error updating assets: {str(e)}"
        logger.error(error_msg)
        return {"updated_count": 0, "errors": [error_msg]}


def get_asset_history(
    guid: Optional[str] = None,
    qualified_name: Optional[str] = None,
    type_name: Optional[str] = None,
    size: int = 10,
    sort_order: str = "DESC",
    include_attributes: Optional[List[Union[str, AtlanField]]] = None,
) -> Dict[str, Any]:
    """
    Get the audit history of an asset by GUID or qualified name.

    Args:
        guid (Optional[str]): GUID of the asset to get history for.
            Either guid or qualified_name must be provided.
        qualified_name (Optional[str]): Qualified name of the asset to get history for.
            Either guid or qualified_name must be provided.
        type_name (Optional[str]): Type name of the asset (required when using qualified_name).
            Examples: "Table", "Column", "DbtModel", "AtlasGlossary"
        size (int): Number of history entries to return. Defaults to 10.
        sort_order (str): Sort order for results. "ASC" for oldest first, "DESC" for newest first.
            Defaults to "DESC".
        include_attributes (List[Union[str, AtlanField]], optional): List of additional attributes to include in results.
            Can be string attribute names or AtlanField objects. These will be added to the default set.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - entityAudits: List of audit entries
            - count: Number of audit entries returned
            - totalCount: Total number of audit entries available
            - errors: List of any errors encountered

    Raises:
        Exception: If there's an error retrieving the asset history
    """
    try:
        # Validate input parameters
        validation_error = validate_asset_history_params(
            guid, qualified_name, type_name, sort_order
        )
        if validation_error:
            logger.error(validation_error)
            return {
                "errors": [validation_error],
                "entityAudits": [],
                "count": 0,
                "totalCount": 0,
            }

        logger.info(
            f"Retrieving asset history with parameters: guid={guid}, qualified_name={qualified_name}, size={size}"
        )

        # Get Atlan client
        client = get_atlan_client()

        # Create sort item
        sort_item = create_sort_item(sort_order)

        # Convert include_attributes from snake_case to camelCase if needed
        if include_attributes:
            include_attributes = convert_attributes_to_camel_case(include_attributes)

        # Create and execute audit search request
        request = create_audit_search_request(
            guid, qualified_name, type_name, size, sort_item, include_attributes
        )
        response = client.audit.search(criteria=request, bulk=False)

        # Process audit results - use current_page() to respect size parameter
        entity_audits = [
            process_audit_result(result, include_attributes)
            for result in response.current_page()
        ]

        result_data = {
            "entityAudits": entity_audits,
            "count": len(entity_audits),
            "totalCount": response.total_count,
            "errors": [],
        }

        logger.info(
            f"Successfully retrieved {len(entity_audits)} audit entries for asset"
        )
        return result_data

    except Exception as e:
        error_msg = f"Error retrieving asset history: {str(e)}"
        logger.error(error_msg)
        logger.exception("Exception details:")
        return {"errors": [error_msg], "entityAudits": [], "count": 0, "totalCount": 0}

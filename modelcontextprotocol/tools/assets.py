import logging
from collections.abc import Mapping
from typing import Any, Dict, List, Optional, Union

from client import get_atlan_client
from pyatlan.model.assets import Asset as AssetModel, File
from pyatlan.model.custom_metadata import CustomMetadataDict
from pyatlan.model.enums import FileType
from .models import CertificateStatus, UpdatableAsset, UpdatableAttribute

# Configure logging
logger = logging.getLogger(__name__)

FILE_TYPE_ALIASES = {
    "pdf": FileType.PDF,
    "doc": FileType.DOC,
    "docx": FileType.DOC,
    "xls": FileType.XLS,
    "xlsx": FileType.XLS,
    "xlsm": FileType.XLSM,
    "excel": FileType.XLS,
    "csv": FileType.CSV,
}


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


def _resolve_file_type(file_type: Union[str, FileType]) -> FileType:
    if isinstance(file_type, FileType):
        return file_type
    if not isinstance(file_type, str):
        raise ValueError("file_type must be a string or FileType enum member.")
    normalized = file_type.strip().lower()
    if normalized in FILE_TYPE_ALIASES:
        return FILE_TYPE_ALIASES[normalized]
    try:
        return FileType[normalized.upper()]
    except KeyError as err:
        raise ValueError(
            f"Unsupported file_type '{file_type}'. "
            "Supported values include 'pdf', 'excel', 'xls', 'xlsx', 'xlsm'."
        ) from err


def _apply_custom_metadata_to_asset(
    asset: File, custom_metadata: Mapping[str, Mapping[str, Any]]
) -> List[str]:
    """
    Apply custom metadata values to an asset.

    Returns:
        List[str]: Names of custom metadata sets that were modified.
    """
    client = get_atlan_client()
    applied_sets: List[str] = []

    for cm_name, attributes in custom_metadata.items():
        if not isinstance(attributes, Mapping):
            raise ValueError(
                f"Custom metadata for '{cm_name}' must be a mapping of attribute names to values."
            )
        cm_dict: CustomMetadataDict = asset.get_custom_metadata(client, cm_name)
        for attr_name, attr_value in attributes.items():
            try:
                cm_dict[attr_name] = attr_value
            except KeyError as exc:
                raise ValueError(
                    f"'{attr_name}' is not a valid attribute for custom metadata set '{cm_name}'."
                ) from exc
        asset.set_custom_metadata(client, cm_dict)
        applied_sets.append(cm_name)

    return applied_sets


def create_unstructured_asset(
    *,
    name: str,
    connection_qualified_name: str,
    file_type: Union[str, FileType],
    file_path: Optional[str] = None,
    description: Optional[str] = None,
    custom_metadata: Optional[Mapping[str, Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Create a File asset in Atlan to represent an unstructured object (PDF, Excel, etc.).

    Args:
        name: Display name of the file asset.
        connection_qualified_name: Qualified name of the Atlan connection where the asset should live.
        file_type: FileType enum member or string alias (pdf, excel, xls, xlsx, xlsm, etc.).
        file_path: Optional path or URI to the underlying document.
        description: Optional human-readable description.
        custom_metadata: Optional mapping of custom metadata sets to attribute/value pairs.

    Returns:
        Dict[str, Any]: Details about the created asset including the assigned GUID and qualified name.
    """

    if not name or not connection_qualified_name:
        raise ValueError("Both 'name' and 'connection_qualified_name' are required.")

    file_type_enum = _resolve_file_type(file_type)
    client = get_atlan_client()

    file_asset = File.creator(
        name=name, connection_qualified_name=connection_qualified_name, file_type=file_type_enum
    )

    if file_path:
        file_asset.file_path = file_path
    if description:
        file_asset.description = description

    applied_cm: List[str] = []
    if custom_metadata:
        applied_cm = _apply_custom_metadata_to_asset(file_asset, custom_metadata)

    response = client.asset.save(file_asset)
    assigned_guid = None
    if response.guid_assignments:
        assigned_guid = response.guid_assignments.get(file_asset.guid)

    created_assets = response.assets_created(File)
    qualified_name = (
        created_assets[0].qualified_name if created_assets and created_assets[0].qualified_name else None
    )

    return {
        "guid": assigned_guid,
        "qualified_name": qualified_name or file_asset.qualified_name,
        "name": name,
        "type_name": file_asset.type_name,
        "file_type": file_type_enum.value,
        "file_path": file_path,
        "custom_metadata_applied": applied_cm,
    }


def read_custom_metadata(
    *,
    guid: Optional[str] = None,
    qualified_name: Optional[str] = None,
    asset_type: str = "Asset",
    custom_metadata_sets: Optional[Union[str, List[str]]] = None,
    include_unset: bool = False,
) -> Dict[str, Any]:
    """
    Retrieve custom metadata values for an asset.

    Args:
        guid: GUID of the target asset.
        qualified_name: Qualified name of the target asset (required if guid is not provided).
        asset_type: The Atlan asset type name (for example, File, Table). Defaults to Asset.
        custom_metadata_sets: Single set name or list of set names to fetch.
            If omitted, all custom metadata sets will be returned.
        include_unset: Whether to include attributes that are defined on the template but currently unset.

    Returns:
        Dict[str, Any]: Asset identifiers and a mapping of custom metadata values.
    """

    if not guid and not qualified_name:
        raise ValueError("Either 'guid' or 'qualified_name' must be provided.")

    try:
        asset_cls = getattr(
            __import__("pyatlan.model.assets", fromlist=[asset_type]), asset_type
        )
    except AttributeError as exc:
        raise ValueError(f"Unknown asset_type '{asset_type}'.") from exc

    client = get_atlan_client()
    attributes = [AssetModel.CUSTOM_ATTRIBUTES]

    if guid:
        asset = client.asset.get_by_guid(
            guid=guid,
            asset_type=asset_cls,
            attributes=attributes,
        )
    else:
        asset = client.asset.get_by_qualified_name(
            qualified_name=qualified_name, asset_type=asset_cls, attributes=attributes
        )

    if isinstance(custom_metadata_sets, str):
        cm_sets = [custom_metadata_sets]
    else:
        cm_sets = custom_metadata_sets

    metadata: Dict[str, Dict[str, Any]] = {}

    def _serialize_custom_metadata(cm_dict: CustomMetadataDict) -> Dict[str, Any]:
        values = dict(cm_dict)
        if include_unset:
            for attr_name in cm_dict.attribute_names:
                values.setdefault(attr_name, None)
        return values

    if cm_sets:
        for cm_name in cm_sets:
            cm_dict = asset.get_custom_metadata(client, cm_name)
            metadata[cm_name] = _serialize_custom_metadata(cm_dict)
    else:
        business_attributes = asset.business_attributes or {}
        for cm_id in business_attributes.keys():
            cm_name = client.custom_metadata_cache.get_name_for_id(cm_id)
            cm_dict = asset.get_custom_metadata(client, cm_name)
            metadata[cm_name] = _serialize_custom_metadata(cm_dict)

    return {
        "guid": asset.guid,
        "qualified_name": asset.qualified_name,
        "custom_metadata": metadata,
    }

import logging
from typing import List, Union, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel  # Or similar BaseModel in your context
from client import get_atlan_client
from .models import (
    UpdatableAsset,
    UpdatableAttribute as ModelsUpdatableAttribute,
    CertificateStatus,
    TermOperation,
    TermOperations,
)
from pyatlan.model.assets import Readme, AtlasGlossaryTerm, AtlasGlossaryCategory
from pyatlan.model.fluent_search import CompoundQuery, FluentSearch
from .tags import retrieve_atlan_tag_by_name

# Initialize logging
logger = logging.getLogger(__name__)

# ---- Extend UpdatableAttribute enum for internal use ----
# Note: This enum uses different values than models.py because asset attributes
# use camelCase (e.g., "userDescription") while the API uses snake_case (e.g., "user_description")
class UpdatableAttribute(str, Enum):
    USER_DESCRIPTION = "userDescription"
    CERTIFICATE_STATUS = "certificateStatus"
    README = "readme"
    TERM = "term"
    ATLAN_TAG = "atlanTag"  # New attribute for Atlan Tag definition updates
    
    @classmethod
    def from_models_enum(cls, models_attr: ModelsUpdatableAttribute):
        """Convert from models.py enum to assets.py enum."""
        mapping = {
            ModelsUpdatableAttribute.USER_DESCRIPTION: cls.USER_DESCRIPTION,
            ModelsUpdatableAttribute.CERTIFICATE_STATUS: cls.CERTIFICATE_STATUS,
            ModelsUpdatableAttribute.README: cls.README,
            ModelsUpdatableAttribute.TERM: cls.TERM,
            ModelsUpdatableAttribute.ATLAN_TAG: cls.ATLAN_TAG,
        }
        return mapping.get(models_attr, models_attr)

# ---- New AtlanTagUpdate model ----
class AtlanTagUpdate(BaseModel):
    name: str
    color: Optional[str] = None
    description: Optional[str] = None

ALLOWED_TAG_COLORS = {"GRAY", "GREEN", "YELLOW", "RED"}
# AtlanTagColor and retrieve_atlan_tag_by_name assumed imported from context

def _perform_atlan_tag_update(client, update_data: AtlanTagUpdate) -> Dict[str, Any]:
    """
    Helper to update an existing Atlan tag definition using AtlanTagUpdate object.
    """
    name = update_data.name
    color = update_data.color
    description = update_data.description

    logger.info(
        f"Updating Atlan tag: name={name}, color={color or 'not provided'}, description={bool(description)}"
    )

    # 1. Validate that name is provided
    if not name or not name.strip():
        error_msg = "Tag name is required and cannot be empty."
        logger.error(error_msg)
        return {"error": error_msg}
    # 2. Validate at least one property
    if color is None and description is None:
        error_msg = "At least one property (color or description) must be provided for update."
        logger.error(error_msg)
        return {"error": error_msg}

    # 3. Retrieve tag by display name
    result = retrieve_atlan_tag_by_name(display_name=name)
    if result.get("error"):
        logger.error(f"Error retrieving tag for update: {result['error']}")
        return {"error": f"Failed to retrieve tag: {result['error']}"}
    if result.get("count", 0) < 1 or not result.get("tags"):
        error_msg = f"Tag with name '{name}' does not exist. Please check the display name."
        logger.error(error_msg)
        return {"error": error_msg}
    existing_tag = result["tags"][0]

    # Retrieve the full definition from the client
    try:
        from pyatlan.model.typedef import AtlanTagDef
        from pyatlan.model.enums import AtlanTypeCategory
        
        # Get all tag definitions and find the one we need
        response = client.typedef.get(type_category=AtlanTypeCategory.CLASSIFICATION)
        all_tag_defs = getattr(response, "atlan_tag_defs", []) or []
        
        tag_def = None
        for tag in all_tag_defs:
            if getattr(tag, "name", None) == existing_tag["internal_name"]:
                tag_def = tag
                break
        
        if not tag_def:
            error_msg = f"Failed to retrieve tag definition for '{name}' (internal={existing_tag['internal_name']})"
            logger.error(error_msg)
            return {"error": error_msg}
    except Exception as e:
        error_msg = f"Error retrieving tag definition for update: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

    # 3a. Validate/convert color if given
    atlan_color_enum = None
    if color is not None:
        color_upper = color.upper()
        if color_upper not in ALLOWED_TAG_COLORS:
            valid_colors = ", ".join(sorted(ALLOWED_TAG_COLORS))
            error_msg = f"Invalid color '{color}'. Only the following colors are allowed: {valid_colors}"
            logger.error(error_msg)
            return {"error": error_msg}
        try:
            from pyatlan.model.enums import AtlanTagColor
            atlan_color_enum = AtlanTagColor[color_upper]
            tag_def.options = tag_def.options or {}
            tag_def.options["color"] = atlan_color_enum.value
            logger.info(f"Updating tag color: {atlan_color_enum.name}")
        except KeyError:
            valid_colors = ", ".join(sorted(ALLOWED_TAG_COLORS))
            error_msg = f"Invalid color '{color}'. Only the following colors are allowed: {valid_colors}"
            logger.error(error_msg)
            return {"error": error_msg}
    # 4. Set description if provided
    if description is not None:
        tag_def.description = description
        logger.info(f"Updating description: {bool(description)}")

    # 5. Update tag through Atlan typedef API
    try:
        response = client.typedef.update(tag_def)
        atlan_tag_defs = getattr(response, "atlan_tag_defs", []) or []
        updated_def = atlan_tag_defs[0] if atlan_tag_defs else None
        if not updated_def:
            error_msg = "Tag update succeeded but no tag definition was returned."
            logger.error(error_msg)
            return {"error": error_msg}
        logger.info(
            f"Successfully updated Atlan tag '{name}' (internal={getattr(updated_def, 'name', None)}, guid={getattr(updated_def, 'guid', None)})"
        )
        # Get updated color from options
        updated_color = None
        if hasattr(updated_def, "options") and updated_def.options:
            color_value = updated_def.options.get("color", "")
            from pyatlan.model.enums import AtlanTagColor
            for color_enum in AtlanTagColor:
                if color_enum.value == color_value:
                    updated_color = color_enum.name
                    break

        return {
            "updated": True,
            "tag": {
                "display_name": getattr(updated_def, "display_name", name),
                "internal_name": getattr(updated_def, "name", None),
                "guid": getattr(updated_def, "guid", None),
                "color": updated_color or (color.upper() if color else existing_tag.get("options", {}).get("color", "N/A")),
                "description": getattr(updated_def, "description", description),
                "options": getattr(updated_def, "options", {}) or {},
            },
            "message": f"Tag '{name}' has been successfully updated.",
        }
    except Exception as e:
        logger.error(f"Error updating Atlan tag '{name}': {e}", exc_info=True)
        return {"error": f"Failed to update tag: {str(e)}"}

def update_assets(
    updatable_assets: Union[UpdatableAsset, List[UpdatableAsset]],
    attribute_name: Union[UpdatableAttribute, ModelsUpdatableAttribute],
    attribute_values: List[Union[str, CertificateStatus, TermOperations, AtlanTagUpdate]],
) -> Dict[str, Any]:
    """
    Update one or multiple assets with different values for attributes, term operations, or Atlan Tag definitions.

    Args:
        updatable_assets (Union[UpdatableAsset, List[UpdatableAsset]]): Asset(s) to update.
            Can be a single UpdatableAsset or a list of UpdatableAssets.
            For asset of type_name=AtlasGlossaryTerm or type_name=AtlasGlossaryCategory, each asset dictionary MUST include a "glossary_guid" key which is the GUID of the glossary that the term belongs to.
        attribute_name (UpdatableAttribute): Name of the attribute to update.
            Supports userDescription, certificateStatus, readme, term, and atlanTag.
        attribute_values (List[Union[str, CertificateStatus, TermOperations, AtlanTagUpdate]]): List of values to set for the attribute.
            For certificateStatus, only VERIFIED, DRAFT, or DEPRECATED are allowed.
            For readme, the value must be a valid Markdown string.
            For term, the value must be a TermOperations object with operation and term_guids.
            For atlanTag, the value must be an AtlanTagUpdate object.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - updated_count: Number of assets or tags successfully updated
            - errors: List of any errors encountered
            - operation: The operation that was performed (for term operations), if applicable
    """
    try:
        # Convert single asset to list for consistent handling
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

        # Normalize attribute_name - handle both enum types by comparing values
        attr_value = attribute_name.value if hasattr(attribute_name, 'value') else str(attribute_name)
        
        # Initialize result tracking
        result = {"updated_count": 0, "errors": []}

        # To track if any "asset" updates (not tags) have been performed
        asset_updates_performed = False

        # Validate certificate status values if applicable
        if attr_value == UpdatableAttribute.CERTIFICATE_STATUS.value or attr_value == ModelsUpdatableAttribute.CERTIFICATE_STATUS.value:
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
            # Handle AtlanTag update at the top
            if attr_value == UpdatableAttribute.ATLAN_TAG.value or attr_value == ModelsUpdatableAttribute.ATLAN_TAG.value:
                tag_update_value = attribute_values[index]
                if not isinstance(tag_update_value, AtlanTagUpdate):
                    error_msg = f"AtlanTag update value must be an AtlanTagUpdate object for index {index}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    continue
                tag_update_result = _perform_atlan_tag_update(client, tag_update_value)
                if tag_update_result.get("updated"):
                    result["updated_count"] += 1
                    logger.info(f"Successfully updated Atlan tag '{tag_update_value.name}'")
                else:
                    # Add error
                    msg = tag_update_result.get("error", f"Unknown error updating tag '{tag_update_value.name}'")
                    logger.error(msg)
                    result["errors"].append(msg)
                # Don't process asset object for this row
                continue

            type_name = updatable_asset.type_name
            qualified_name = updatable_asset.qualified_name
            asset_cls = getattr(
                __import__("pyatlan.model.assets", fromlist=[type_name]), type_name
            )

            # Special handling for Glossary Term updates
            if (
                updatable_asset.type_name == AtlasGlossaryTerm.__name__
                or updatable_asset.type_name == AtlasGlossaryCategory.__name__
            ):
                asset = asset_cls.updater(
                    qualified_name=updatable_asset.qualified_name,
                    name=updatable_asset.name,
                    glossary_guid=updatable_asset.glossary_guid,
                )
            else:
                asset = asset_cls.updater(
                    qualified_name=updatable_asset.qualified_name,
                    name=updatable_asset.name,
                )

            # Special handling for README updates
            if attr_value == UpdatableAttribute.README.value or attr_value == ModelsUpdatableAttribute.README.value:
                # Get the current readme content for the asset
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
                    asset_updates_performed = True
            elif attr_value == UpdatableAttribute.TERM.value or attr_value == ModelsUpdatableAttribute.TERM.value:
                # Special handling for term operations
                term_value = attribute_values[index]
                if not isinstance(term_value, TermOperations):
                    error_msg = f"Term value must be a TermOperations object for asset {updatable_asset.qualified_name}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    continue

                term_operation = TermOperation(term_value.operation.lower())
                term_guids = term_value.term_guids

                # Create term references
                term_refs = [
                    AtlasGlossaryTerm.ref_by_guid(guid=guid) for guid in term_guids
                ]

                try:
                    # Perform the appropriate term operation
                    if term_operation == TermOperation.APPEND:
                        client.asset.append_terms(
                            asset_type=asset_cls,
                            qualified_name=updatable_asset.qualified_name,
                            terms=term_refs,
                        )
                    elif term_operation == TermOperation.REPLACE:
                        client.asset.replace_terms(
                            asset_type=asset_cls,
                            qualified_name=updatable_asset.qualified_name,
                            terms=term_refs,
                        )
                    elif term_operation == TermOperation.REMOVE:
                        client.asset.remove_terms(
                            asset_type=asset_cls,
                            qualified_name=updatable_asset.qualified_name,
                            terms=term_refs,
                        )

                    result["updated_count"] += 1
                    logger.info(
                        f"Successfully {term_operation.value}d terms on asset: {updatable_asset.qualified_name}"
                    )
                    asset_updates_performed = True

                except Exception as e:
                    error_msg = f"Error updating terms on asset {updatable_asset.qualified_name}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
            else:
                # Regular attribute update flow
                # Use the local enum value for asset attributes (camelCase)
                local_attr_name = UpdatableAttribute(attr_value) if attr_value in [e.value for e in UpdatableAttribute] else None
                if local_attr_name:
                    setattr(asset, local_attr_name.value, attribute_values[index])
                else:
                    # Fallback: try to use the value directly
                    setattr(asset, attr_value, attribute_values[index])
                assets.append(asset)
                asset_updates_performed = True

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

        # Process response
        if asset_updates_performed and len(assets) > 0:
            response = client.asset.save(assets)
            result["updated_count"] += len(response.guid_assignments)
            logger.info(f"Successfully updated {len(response.guid_assignments)} assets")
        elif not asset_updates_performed:
            logger.info(f"Processed only Atlan tag updates; no asset.save() invoked.")

        return result

    except Exception as e:
        error_msg = f"Error updating assets: {str(e)}"
        logger.error(error_msg)
        return {"updated_count": 0, "errors": [error_msg]}

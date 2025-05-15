"""Implementation of custom metadata, badge, and metadata management functionality."""

import logging
from typing import List, Optional, Dict, Any
from pyatlan.model.typedef import AttributeDef, CustomMetadataDef
from pyatlan.model.enums import (
    AtlanCustomAttributePrimitiveType,
    BadgeConditionColor,
    BadgeComparisonOperator,
)
from pyatlan.model.assets import Badge
from pyatlan.model.structs import BadgeCondition

from client import get_atlan_client

# Configure logging
logger = logging.getLogger(__name__)


def create_custom_metadata(
    display_name: str,
    attributes: List[Dict[str, Any]],
    description: Optional[str] = None,
    emoji: Optional[str] = None,
    logo_url: Optional[str] = None,
    locked: bool = False,
) -> Dict[str, Any]:
    """Create a custom metadata definition in Atlan.

    Args:
        display_name (str): Display name for the custom metadata
        attributes (List[Dict[str, Any]]): List of attribute definitions. Each attribute should have:
            - display_name (str): Display name for the attribute
            - attribute_type (str): Type of the attribute (from AtlanCustomAttributePrimitiveType)
            - description (str, optional): Description of the attribute
            - multi_valued (bool, optional): Whether the attribute can have multiple values
            - options_name (str, optional): Name of options for enumerated types
        description (str, optional): Description of the custom metadata
        emoji (str, optional): Emoji to use as the logo
        logo_url (str, optional): URL to use for the logo
        locked (bool, optional): Whether the custom metadata definition should be locked

    Returns:
        Dict[str, Any]: Response from the creation request containing:
            - created: Boolean indicating if creation was successful
            - guid: GUID of the created custom metadata definition
            - error: Error message if creation failed
    """
    try:
        logger.info(f"Creating custom metadata definition: {display_name}")

        # Get Atlan client first to fail early if there are connection issues
        try:
            client = get_atlan_client()
        except Exception as e:
            error_msg = f"Failed to initialize Atlan client: {str(e)}"
            logger.error(error_msg)
            return {"created": False, "error": error_msg}

        # Create base custom metadata definition
        logger.debug("Creating base custom metadata definition")
        cm_def = CustomMetadataDef.create(display_name=display_name)

        # Set custom metadata description if provided
        if description:
            logger.debug(f"Setting custom metadata description: {description}")
            cm_def.description = description

        # Add attribute definitions
        attribute_defs = []
        for attr in attributes:
            try:
                # Parse and validate attribute type
                try:
                    attr_type = getattr(
                        AtlanCustomAttributePrimitiveType,
                        attr["attribute_type"].upper(),
                    )
                except (AttributeError, KeyError):
                    error_msg = f"Invalid attribute type for {attr.get('display_name', 'unknown')}: {attr.get('attribute_type')}"
                    logger.error(error_msg)
                    return {"created": False, "error": error_msg}

                # Create attribute definition
                attr_def = AttributeDef.create(
                    display_name=attr["display_name"],
                    attribute_type=attr_type,
                    options_name=attr.get("options_name"),
                    multi_valued=attr.get("multi_valued", False),
                )

                # Set attribute description if provided
                if attr.get("description"):
                    logger.debug(
                        f"Setting description for attribute {attr['display_name']}: {attr['description']}"
                    )
                    attr_def.description = attr["description"]

                attribute_defs.append(attr_def)
                logger.debug(
                    f"Added attribute: {attr['display_name']} of type {attr_type}"
                )
            except KeyError as e:
                error_msg = f"Missing required field in attribute definition: {str(e)}"
                logger.error(error_msg)
                return {"created": False, "error": error_msg}

        # Set attributes on custom metadata definition
        cm_def.attribute_defs = attribute_defs
        logger.debug(f"Added {len(attribute_defs)} attribute definitions")

        # Set logo options
        if emoji:
            logger.debug(f"Setting emoji logo: {emoji}")
            try:
                cm_def.options = CustomMetadataDef.Options.with_logo_as_emoji(
                    emoji=emoji, locked=locked
                )
            except Exception as e:
                error_msg = f"Failed to set emoji logo: {str(e)}"
                logger.error(error_msg)
                return {"created": False, "error": error_msg}
        elif logo_url:
            logger.debug(f"Setting logo URL: {logo_url}")
            try:
                cm_def.options = CustomMetadataDef.Options.with_logo_from_url(
                    url=logo_url, locked=locked
                )
            except Exception as e:
                error_msg = f"Failed to set logo URL: {str(e)}"
                logger.error(error_msg)
                return {"created": False, "error": error_msg}

        # Create the custom metadata definition
        logger.info("Sending creation request to Atlan")
        try:
            response = client.typedef.create(cm_def)
            if response and hasattr(response, "custom_metadata_defs"):
                custom_metadata_defs = response.custom_metadata_defs
                if isinstance(custom_metadata_defs, list) and custom_metadata_defs:
                    first_def = custom_metadata_defs[0]
                    if hasattr(first_def, "guid"):
                        logger.info(
                            f"Custom metadata definition created with GUID: {first_def.guid}"
                        )
                        return {"created": True, "guid": first_def.guid}

            # If we get here, the response didn't have the expected structure
            logger.error("Unexpected response structure")
            logger.debug(f"Response: {response}")
            return {
                "created": False,
                "error": "Custom metadata was created but unable to retrieve GUID",
            }
        except Exception as e:
            error_msg = f"Failed to create custom metadata: {str(e)}"
            logger.error(error_msg)
            logger.debug("Custom metadata definition that failed:", cm_def)
            return {"created": False, "error": error_msg}

    except Exception as e:
        error_msg = f"Unexpected error creating custom metadata: {str(e)}"
        logger.error(error_msg)
        logger.exception("Exception details:")
        return {"created": False, "error": error_msg}


def get_custom_metadata(name: str) -> Dict[str, Any]:
    """Retrieve an existing custom metadata definition.

    Args:
        name (str): Name of the custom metadata to retrieve

    Returns:
        Dict[str, Any]: Response containing:
            - found: Boolean indicating if metadata was found
            - metadata: Custom metadata definition if found
            - error: Error message if retrieval failed
    """
    try:
        logger.info(f"Retrieving custom metadata: {name}")
        client = get_atlan_client()
        metadata = client.custom_metadata_cache.get_custom_metadata_def(name=name)

        if metadata:
            logger.info(f"Found custom metadata: {name}")
            return {"found": True, "metadata": metadata}

        logger.info(f"Custom metadata not found: {name}")
        return {"found": False, "error": f"Custom metadata '{name}' not found"}

    except Exception as e:
        error_msg = f"Error retrieving custom metadata: {str(e)}"
        logger.error(error_msg)
        logger.exception("Exception details:")
        return {"found": False, "error": error_msg}


def update_custom_metadata(
    name: str,
    add_attributes: Optional[List[Dict[str, Any]]] = None,
    modify_attributes: Optional[Dict[str, Dict[str, Any]]] = None,
    remove_attributes: Optional[List[str]] = None,
    archived_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Update an existing custom metadata definition.

    Args:
        name (str): Name of the custom metadata to update
        add_attributes (List[Dict[str, Any]], optional): New attributes to add. Each attribute should have:
            - display_name (str): Display name for the attribute
            - attribute_type (str): Type of the attribute (from AtlanCustomAttributePrimitiveType)
            - description (str, optional): Description of the attribute
            - multi_valued (bool, optional): Whether the attribute can have multiple values
            - options_name (str, optional): Name of options for enumerated types
        modify_attributes (Dict[str, Dict[str, Any]], optional): Attributes to modify, keyed by display name
        remove_attributes (List[str], optional): Display names of attributes to remove
        archived_by (str, optional): Username of person archiving attributes (required for removal)

    Returns:
        Dict[str, Any]: Response containing:
            - updated: Boolean indicating if update was successful
            - error: Error message if update failed
    """
    try:
        logger.info(f"Starting update for custom metadata: {name}")

        # Get existing metadata
        existing_result = get_custom_metadata(name)
        if not existing_result.get("found"):
            return {
                "updated": False,
                "error": existing_result.get(
                    "error", f"Custom metadata '{name}' not found"
                ),
            }

        existing = existing_result["metadata"]
        attrs = existing.attribute_defs or []
        modified = False

        # Add new attributes
        if add_attributes:
            logger.info(f"Adding {len(add_attributes)} new attributes")
            for attr in add_attributes:
                try:
                    # Parse and validate attribute type
                    try:
                        attr_type = getattr(
                            AtlanCustomAttributePrimitiveType,
                            attr["attribute_type"].upper(),
                        )
                    except (AttributeError, KeyError):
                        error_msg = f"Invalid attribute type for {attr.get('display_name', 'unknown')}: {attr.get('attribute_type')}"
                        logger.error(error_msg)
                        return {"updated": False, "error": error_msg}

                    # Create attribute definition
                    attr_def = AttributeDef.create(
                        display_name=attr["display_name"],
                        attribute_type=attr_type,
                        options_name=attr.get("options_name"),
                        multi_valued=attr.get("multi_valued", False),
                    )

                    # Set description if provided
                    if attr.get("description"):
                        logger.debug(
                            f"Setting description for attribute {attr['display_name']}"
                        )
                        attr_def.description = attr["description"]

                    attrs.append(attr_def)
                    modified = True

                except KeyError as e:
                    error_msg = (
                        f"Missing required field in attribute definition: {str(e)}"
                    )
                    logger.error(error_msg)
                    return {"updated": False, "error": error_msg}

        # Modify existing attributes
        if modify_attributes:
            logger.info(f"Modifying {len(modify_attributes)} attributes")
            revised = []
            for attr in attrs:
                if attr.display_name in modify_attributes:
                    changes = modify_attributes[attr.display_name]
                    if "display_name" in changes:
                        attr.display_name = changes["display_name"]
                    if "description" in changes:
                        attr.description = changes["description"]
                    modified = True
                revised.append(attr)
            attrs = revised

        # Remove attributes
        if remove_attributes:
            if not archived_by:
                return {
                    "updated": False,
                    "error": "archived_by is required when removing attributes",
                }

            logger.info(f"Removing {len(remove_attributes)} attributes")
            revised = []
            for attr in attrs:
                if attr.display_name in remove_attributes:
                    attr.archive(by=archived_by)
                    modified = True
                revised.append(attr)
            attrs = revised

        if not modified:
            logger.info("No changes were made to the custom metadata")
            return {"updated": True, "message": "No changes were required"}

        # Update the metadata definition
        existing.attribute_defs = attrs

        try:
            logger.info("Sending update request to Atlan")
            client = get_atlan_client()
            response = client.typedef.update(existing)

            if response:
                logger.info("Custom metadata updated successfully")
                return {"updated": True}

            error_msg = "Failed to update custom metadata - no response"
            logger.error(error_msg)
            return {"updated": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Error updating custom metadata: {str(e)}"
            logger.error(error_msg)
            logger.exception("Exception details:")
            return {"updated": False, "error": error_msg}

    except Exception as e:
        error_msg = f"Unexpected error updating custom metadata: {str(e)}"
        logger.error(error_msg)
        logger.exception("Exception details:")
        return {"updated": False, "error": error_msg}


def create_badge(
    name: str,
    metadata_name: str,
    attribute_name: str,
    display_name: Optional[str] = None,
    description: Optional[str] = None,
    emoji: Optional[str] = None,
    logo_url: Optional[str] = None,
    badge_conditions: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Create a badge for a custom metadata attribute with optional conditions.

    Args:
        name (str): Unique name for the badge
        metadata_name (str): Name of the custom metadata definition
        attribute_name (str): Name of the attribute to show in the badge
        display_name (str, optional): Display name for the badge
        description (str, optional): Description of the badge
        emoji (str, optional): Emoji to use as the badge icon
        logo_url (str, optional): URL to use for the badge icon
        badge_conditions (List[Dict[str, Any]], optional): List of conditions for the badge.
            Each condition should contain:
            - operator: BadgeComparisonOperator (e.g. "GTE", "LT")
            - value: The value to compare against
            - color: BadgeConditionColor (e.g. "GREEN", "YELLOW", "RED")

    Returns:
        Dict[str, Any]: Response containing:
            - created: Boolean indicating if creation was successful
            - guid: GUID of the created badge
            - error: Error message if creation failed
    """
    try:
        logger.info(f"Creating badge '{name}' for {metadata_name}.{attribute_name}")

        # Get Atlan client
        client = get_atlan_client()

        # Handle badge with conditions vs simple badge
        if badge_conditions:
            logger.debug(f"Creating badge with {len(badge_conditions)} conditions")

            conditions = []
            for cond in badge_conditions:
                try:
                    operator = getattr(
                        BadgeComparisonOperator, cond["operator"].upper()
                    )
                    color = getattr(BadgeConditionColor, cond["color"].upper())

                    condition = BadgeCondition.create(
                        badge_condition_operator=operator,
                        badge_condition_value=str(cond["value"]),
                        badge_condition_colorhex=color,
                    )
                    conditions.append(condition)
                except (KeyError, AttributeError) as e:
                    error_msg = f"Invalid badge condition: {str(e)}"
                    logger.error(error_msg)
                    return {"created": False, "error": error_msg}

            # Create badge with conditions
            badge = Badge.creator(
                name=name,
                cm_name=metadata_name,
                cm_attribute=attribute_name,
                badge_conditions=conditions,
            )

            # Set optional fields
            if description:
                badge.user_description = description

            # Save badge
            try:
                logger.debug("Saving badge with conditions")
                response = client.asset.save(badge)
                assets = response.assets_created(asset_type=Badge)

                if assets:
                    logger.info(f"Badge created with GUID: {assets[0].guid}")
                    return {"created": True, "guid": assets[0].guid}
                else:
                    error_msg = "Badge was created but no GUID was returned"
                    logger.error(error_msg)
                    return {"created": False, "error": error_msg}

            except Exception as e:
                error_msg = f"Failed to save badge: {str(e)}"
                logger.error(error_msg)
                return {"created": False, "error": error_msg}

        else:
            # Create simple badge without conditions
            try:
                logger.info(
                    f"Creating simple badge '{name}' for {metadata_name}.{attribute_name}"
                )

                # Get custom metadata definition first
                try:
                    metadata = client.custom_metadata_cache.get_custom_metadata_def(
                        name=metadata_name
                    )
                    if not metadata:
                        error_msg = f"Custom metadata '{metadata_name}' not found"
                        logger.error(error_msg)
                        return {"created": False, "error": error_msg}
                except Exception as e:
                    error_msg = f"Error retrieving custom metadata: {str(e)}"
                    logger.error(error_msg)
                    return {"created": False, "error": error_msg}

                # Verify attribute exists
                attr_def = None
                for attr in metadata.attribute_defs:
                    if attr.display_name == attribute_name:
                        attr_def = attr
                        break

                if not attr_def:
                    error_msg = f"Attribute '{attribute_name}' not found in custom metadata '{metadata_name}'"
                    logger.error(error_msg)
                    return {"created": False, "error": error_msg}

                # Create badge
                badge = Badge.creator(
                    name=name, cm_name=metadata_name, cm_attribute=attribute_name
                )

                # Set description if provided
                if description:
                    badge.user_description = description

                # Save badge
                try:
                    logger.debug("Saving simple badge")
                    response = client.asset.save(badge)
                    assets = response.assets_created(asset_type=Badge)

                    if assets:
                        logger.info(f"Badge created with GUID: {assets[0].guid}")
                        return {"created": True, "guid": assets[0].guid}
                    else:
                        error_msg = "Badge was created but no GUID was returned"
                        logger.error(error_msg)
                        return {"created": False, "error": error_msg}

                except Exception as e:
                    error_msg = f"Failed to save badge: {str(e)}"
                    logger.error(error_msg)
                    return {"created": False, "error": error_msg}

            except Exception as e:
                error_msg = f"Unexpected error creating badge: {str(e)}"
                logger.error(error_msg)
                logger.exception("Exception details:")
                return {"created": False, "error": error_msg}

    except Exception as e:
        error_msg = f"Unexpected error creating badge: {str(e)}"
        logger.error(error_msg)
        logger.exception("Exception details:")
        return {"created": False, "error": error_msg}


def update_badge(
    name: str,
    display_name: Optional[str] = None,
    description: Optional[str] = None,
    emoji: Optional[str] = None,
    logo_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Update an existing badge definition.

    Args:
        name (str): Name of the badge to update
        display_name (str, optional): New display name for the badge
        description (str, optional): New description of the badge
        emoji (str, optional): New emoji to use as the badge icon
        logo_url (str, optional): New URL to use for the badge icon

    Returns:
        Dict[str, Any]: Response containing:
            - updated: Boolean indicating if update was successful
            - error: Error message if update failed
    """
    try:
        logger.info(f"Updating badge: {name}")

        # Get Atlan client
        client = get_atlan_client()

        # Get existing badge definition
        try:
            badge_defs = client.typedef.get_badge_defs()
            existing = None
            for badge in badge_defs:
                if badge.name == name:
                    existing = badge
                    break

            if not existing:
                error_msg = f"Badge '{name}' not found"
                logger.error(error_msg)
                return {"updated": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Error retrieving badge: {str(e)}"
            logger.error(error_msg)
            return {"updated": False, "error": error_msg}

        modified = False

        # Update display name if provided
        if display_name:
            logger.debug(f"Updating display name to: {display_name}")
            existing.display_name = display_name
            modified = True

        # Update description if provided
        if description:
            logger.debug("Updating description")
            existing.description = description
            modified = True

        # Update logo options if provided
        if emoji:
            logger.debug(f"Updating to emoji logo: {emoji}")
            try:
                existing.options = CustomMetadataDef.Options.with_logo_as_emoji(
                    emoji=emoji
                )
                modified = True
            except Exception as e:
                error_msg = f"Failed to update emoji logo: {str(e)}"
                logger.error(error_msg)
                return {"updated": False, "error": error_msg}
        elif logo_url:
            logger.debug(f"Updating to logo URL: {logo_url}")
            try:
                existing.options = CustomMetadataDef.Options.with_logo_from_url(
                    url=logo_url
                )
                modified = True
            except Exception as e:
                error_msg = f"Failed to update logo URL: {str(e)}"
                logger.error(error_msg)
                return {"updated": False, "error": error_msg}

        if not modified:
            logger.info("No changes were made to the badge")
            return {"updated": True, "message": "No changes were required"}

        # Update the badge
        logger.info("Sending badge update request to Atlan")
        try:
            response = client.typedef.update(existing)

            if response:
                logger.info("Badge updated successfully")
                return {"updated": True}

            error_msg = "Failed to update badge - no response"
            logger.error(error_msg)
            return {"updated": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Failed to update badge: {str(e)}"
            logger.error(error_msg)
            return {"updated": False, "error": error_msg}

    except Exception as e:
        error_msg = f"Unexpected error updating badge: {str(e)}"
        logger.error(error_msg)
        logger.exception("Exception details:")
        return {"updated": False, "error": error_msg}


def delete_badge(guid: str) -> Dict[str, Any]:
    """Delete a badge completely.

    Args:
        guid (str): GUID of the badge to delete

    Returns:
        Dict[str, Any]: Response containing:
            - deleted: Boolean indicating if deletion was successful
            - error: Error message if deletion failed
    """
    try:
        logger.info(f"Deleting badge with GUID: {guid}")
        client = get_atlan_client()

        try:
            response = client.asset.purge_by_guid(guid)

            if response:
                logger.info("Badge deleted successfully")
                return {"deleted": True}

            error_msg = "Failed to delete badge - no response"
            logger.error(error_msg)
            return {"deleted": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Failed to delete badge: {str(e)}"
            logger.error(error_msg)
            return {"deleted": False, "error": error_msg}

    except Exception as e:
        error_msg = f"Unexpected error deleting badge: {str(e)}"
        logger.error(error_msg)
        logger.exception("Exception details:")
        return {"deleted": False, "error": error_msg}

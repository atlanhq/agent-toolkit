import logging
from typing import Optional, Dict, Any, List

from client import get_atlan_client
from pyatlan.model.enums import AtlanTagColor, AtlanTypeCategory
from pyatlan.model.typedef import AtlanTagDef

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
#  retrieve_atlan_tag_by_name  (new public function)
# -------------------------------------------------------------------------
def retrieve_atlan_tag_by_name(display_name: Optional[str] = None, color: Optional[str] = None, description_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve an Atlan tag definition by displayName and/or color, OR list all existing tags.

    Args:
        display_name (str, optional):
            - If provided: filter by matching displayName.
            - If omitted: no displayName filter applied.
        color (str, optional):
            - If provided: filter by matching color (case-insensitive).
            - If omitted: no color filter applied.
        description_filter (str, optional):
            - If "empty": filter tags with empty or None descriptions.
            - If "not_empty": filter tags with non-empty descriptions.
            - If omitted: no description filter applied.

    Returns:
        Dict[str, Any]:
            {
                "tags": [ ... list of tag objects ... ],
                "count": <int>,
                "error": None | "<message>"
            }
    """

    client = get_atlan_client()

    filter_parts = []
    if display_name:
        filter_parts.append(f"displayName='{display_name}'")
    if color:
        filter_parts.append(f"color='{color}'")
    if description_filter:
        filter_parts.append(f"description_filter='{description_filter}'")
    
    if filter_parts:
        logger.info(f"Retrieving Atlan tags with {', '.join(filter_parts)}")
    else:
        logger.info("Retrieving ALL existing Atlan tags (no filters provided).")

    try:
        response = client.typedef.get(type_category=AtlanTypeCategory.CLASSIFICATION)
        all_tag_defs: List[AtlanTagDef] = getattr(response, "atlan_tag_defs", []) or []

        logger.debug(f"Retrieved {len(all_tag_defs)} tag definitions from typedefs.")

        # Apply filters
        matches = all_tag_defs
        
        if display_name:
            matches = [
                tag_def for tag_def in matches
                if getattr(tag_def, "display_name", None) == display_name
            ]
        
        if color:
            color_lower = color.lower()
            matches = [
                tag_def for tag_def in matches
                if (getattr(tag_def, "options", {}) or {}).get("color", "").lower() == color_lower
            ]
        
        if description_filter:
            if description_filter.lower() == "empty":
                matches = [
                    tag_def for tag_def in matches
                    if not getattr(tag_def, "description", None) or getattr(tag_def, "description", "").strip() == ""
                ]
            elif description_filter.lower() == "not_empty":
                matches = [
                    tag_def for tag_def in matches
                    if getattr(tag_def, "description", None) and getattr(tag_def, "description", "").strip() != ""
                ]
            else:
                logger.warning(f"Invalid description_filter value: '{description_filter}'. Valid values are 'empty' or 'not_empty'. Ignoring filter.")

        return {
            "tags": [
                {
                    "display_name": t.display_name,
                    "internal_name": getattr(t, "name", None),
                    "guid": getattr(t, "guid", None),
                    "description": getattr(t, "description", None),
                    "options": getattr(t, "options", {}) or {},
                }
                for t in matches
            ],
            "count": len(matches),
            "error": None,
        }

    except Exception as e:
        logger.error(
            "Error retrieving Atlan tag definitions: %s", e, exc_info=True
        )
        return {"tags": [], "count": 0, "error": str(e)}


# -------------------------------------------------------------------------
#  create_atlan_tag  (create new Atlan tag)
# -------------------------------------------------------------------------
def create_atlan_tag(
    name: str,
    color: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new Atlan tag definition.
    
    Process:
    1. Check if a tag with the same name already exists
    2. If it exists, inform the customer that the tag already exists
    3. If it doesn't exist, create the tag

    Args:
        name (str): Human-readable display name of the tag (required).
        color (str, optional): Color for the tag. Defaults to BLACK if not provided.
            Valid colors: BLACK, BLUE, BROWN, CYAN, GREEN, GREY, MAGENTA, ORANGE, PINK, PURPLE, RED, YELLOW
        description (str, optional): Description of the tag.

    Returns:
        Dict[str, Any]:
            - If tag exists: {"exists": True, "created": False, "tag": {...}, "message": "..."}
            - If created: {"exists": False, "created": True, "tag": {...}}
            - If error: {"error": "error message"}
    """

    logger.info(
        f"Creating Atlan tag: name={name}, color={color or 'BLACK (default)'}, "
        f"description={bool(description)}"
    )

    # Validate that name is provided
    if not name or not name.strip():
        error_msg = "Tag name is required and cannot be empty."
        logger.error(error_msg)
        return {"error": error_msg}

    client = get_atlan_client()

    # ------------------------------------------------------------------
    # 1. Check if tag already exists by displayName
    # ------------------------------------------------------------------
    result = retrieve_atlan_tag_by_name(display_name=name)

    if result["error"]:
        # propagate retrieval error
        logger.error(f"Error checking for existing tag: {result['error']}")
        return {"error": f"Failed to check if tag exists: {result['error']}"}

    if result["count"] > 0:
        # Tag already exists — inform the customer
        existing = result["tags"][0]

        logger.info(
            f"Tag '{name}' already exists (internal={existing['internal_name']}, "
            f"guid={existing['guid']})"
        )

        return {
            "exists": True,
            "created": False,
            "tag": existing,
            "message": f"A tag with the name '{name}' already exists. Tag GUID: {existing.get('guid', 'N/A')}",
        }

    # ------------------------------------------------------------------
    # 2. Determine color enum (optional, defaults to BLACK)
    # ------------------------------------------------------------------
    if not color:
        atlan_color_enum = AtlanTagColor.BLACK
    else:
        try:
            atlan_color_enum = AtlanTagColor[color.upper()]
        except KeyError:
            valid_colors = ", ".join([c.name for c in AtlanTagColor])
            msg = f"Invalid color '{color}'. Valid colors are: {valid_colors}"
            logger.error(msg)
            return {"error": msg}

    # ------------------------------------------------------------------
    # 3. Build minimal AtlanTagDef object (as per Atlan documentation)
    # ------------------------------------------------------------------
    try:
        tag_def = AtlanTagDef.create(
            name=name,
            color=atlan_color_enum,
        )

        if description:
            tag_def.description = description

        logger.debug(f"Constructed AtlanTagDef for creation: {tag_def}")

    except Exception as e:
        logger.error(
            f"Failed to construct AtlanTagDef for name={name}: {e}",
            exc_info=True,
        )
        return {"error": f"Failed to create tag definition: {str(e)}"}

    # ------------------------------------------------------------------
    # 4. Create tag through Atlan typedef API
    # ------------------------------------------------------------------
    try:
        response = client.typedef.create(tag_def)
        # Access the created tag definition from the response object
        atlan_tag_defs = getattr(response, "atlan_tag_defs", []) or []
        created_def = atlan_tag_defs[0] if atlan_tag_defs else None

        if not created_def:
            error_msg = "Tag creation succeeded but no tag definition was returned."
            logger.error(error_msg)
            return {"error": error_msg}

        logger.info(
            f"Successfully created Atlan tag '{name}' "
            f"(internal={getattr(created_def, 'name', None)}, "
            f"guid={getattr(created_def, 'guid', None)})"
        )

        return {
            "exists": False,
            "created": True,
            "tag": {
                "display_name": getattr(created_def, "display_name", name),
                "internal_name": getattr(created_def, "name", None),
                "guid": getattr(created_def, "guid", None),
                "color": atlan_color_enum.name,
                "description": getattr(created_def, "description", description),
                "options": getattr(created_def, "options", {}) or {},
            },
            "message": f"Tag '{name}' has been successfully created.",
        }

    except Exception as e:
        logger.error(
            f"Error creating Atlan tag '{name}': {e}", exc_info=True
        )
        return {"error": f"Failed to create tag: {str(e)}"}


# -------------------------------------------------------------------------
#  update_atlan_tag  (update existing Atlan tag)
# -------------------------------------------------------------------------
def update_atlan_tag(
    name: str,
    color: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update an existing Atlan tag definition.
    
    Process:
    1. Check if a tag with the given name exists
    2. If it doesn't exist, return an error
    3. If it exists, retrieve the tag definition and update the specified properties
    4. Only color and description can be updated
    
    Args:
        name (str): Human-readable display name of the tag to update (required).
        color (str, optional): New color for the tag.
            Valid colors: BLACK, BLUE, BROWN, CYAN, GREEN, GREY, MAGENTA, ORANGE, PINK, PURPLE, RED, YELLOW
        description (str, optional): New description for the tag.
    
    Returns:
        Dict[str, Any]:
            - If tag doesn't exist: {"error": "error message"}
            - If updated: {"updated": True, "tag": {...}, "message": "..."}
            - If error: {"error": "error message"}
    """
    
    logger.info(
        f"Updating Atlan tag: name={name}, color={color or 'not provided'}, "
        f"description={bool(description)}"
    )
    
    # Validate that name is provided
    if not name or not name.strip():
        error_msg = "Tag name is required and cannot be empty."
        logger.error(error_msg)
        return {"error": error_msg}
    
    # Validate that at least one property is provided for update
    if not color and description is None:
        error_msg = "At least one property (color or description) must be provided for update."
        logger.error(error_msg)
        return {"error": error_msg}
    
    client = get_atlan_client()
    
    # ------------------------------------------------------------------
    # 1. Check if tag exists by displayName
    # ------------------------------------------------------------------
    result = retrieve_atlan_tag_by_name(display_name=name)
    
    if result["error"]:
        logger.error(f"Error checking for existing tag: {result['error']}")
        return {"error": f"Failed to check if tag exists: {result['error']}"}
    
    if result["count"] == 0:
        error_msg = f"Tag with name '{name}' does not exist. Cannot update a non-existent tag."
        logger.error(error_msg)
        return {"error": error_msg}
    
    # Get the existing tag
    existing_tag = result["tags"][0]
    internal_name = existing_tag.get("internal_name")
    
    if not internal_name:
        error_msg = f"Tag '{name}' exists but internal name is missing. Cannot update."
        logger.error(error_msg)
        return {"error": error_msg}
    
    logger.info(
        f"Found tag '{name}' (internal={internal_name}, guid={existing_tag.get('guid')})"
    )
    
    # ------------------------------------------------------------------
    # 2. Retrieve the full tag definition by internal name
    # ------------------------------------------------------------------
    try:
        tag_def = client.typedef.get_by_name(internal_name)
        
        if not tag_def:
            error_msg = f"Failed to retrieve tag definition for '{name}' (internal={internal_name})"
            logger.error(error_msg)
            return {"error": error_msg}
        
        logger.debug(f"Retrieved tag definition for update: {tag_def}")
        
    except Exception as e:
        logger.error(
            f"Error retrieving tag definition for '{name}': {e}", exc_info=True
        )
        return {"error": f"Failed to retrieve tag definition: {str(e)}"}
    
    # ------------------------------------------------------------------
    # 3. Update color if provided
    # ------------------------------------------------------------------
    if color:
        try:
            atlan_color_enum = AtlanTagColor[color.upper()]
            # Update the color in the options
            if not hasattr(tag_def, "options") or tag_def.options is None:
                tag_def.options = {}
            tag_def.options["color"] = atlan_color_enum.value
            logger.info(f"Updating color to {color.upper()}")
        except KeyError:
            valid_colors = ", ".join([c.name for c in AtlanTagColor])
            msg = f"Invalid color '{color}'. Valid colors are: {valid_colors}"
            logger.error(msg)
            return {"error": msg}
    
    # ------------------------------------------------------------------
    # 4. Update description if provided
    # ------------------------------------------------------------------
    if description is not None:
        tag_def.description = description
        logger.info(f"Updating description: {bool(description)}")
    
    # ------------------------------------------------------------------
    # 5. Update tag through Atlan typedef API
    # ------------------------------------------------------------------
    try:
        response = client.typedef.update(tag_def)
        # Access the updated tag definition from the response object
        atlan_tag_defs = getattr(response, "atlan_tag_defs", []) or []
        updated_def = atlan_tag_defs[0] if atlan_tag_defs else None
        
        if not updated_def:
            error_msg = "Tag update succeeded but no tag definition was returned."
            logger.error(error_msg)
            return {"error": error_msg}
        
        logger.info(
            f"Successfully updated Atlan tag '{name}' "
            f"(internal={getattr(updated_def, 'name', None)}, "
            f"guid={getattr(updated_def, 'guid', None)})"
        )
        
        # Get updated color from options
        updated_color = None
        if hasattr(updated_def, "options") and updated_def.options:
            color_value = updated_def.options.get("color", "")
            # Find the enum value that matches
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
        logger.error(
            f"Error updating Atlan tag '{name}': {e}", exc_info=True
        )
        return {"error": f"Failed to update tag: {str(e)}"}

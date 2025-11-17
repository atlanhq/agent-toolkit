import logging
from typing import Optional, Dict, Any, List

from client import get_atlan_client
from pyatlan.model.enums import AtlanTagColor, AtlanTypeCategory
from pyatlan.model.typedef import AtlanTagDef

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
#  retrieve_tag_by_name  (new public function)
# -------------------------------------------------------------------------
def retrieve_tag_by_name(display_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve an Atlan tag definition by displayName, OR list all existing tags.

    Args:
        display_name (str, optional):
            - If provided: return the matching Atlan tag.
            - If omitted: return ALL existing Atlan tag definitions.

    Returns:
        Dict[str, Any]:
            {
                "tags": [ ... list of tag objects ... ],
                "count": <int>,
                "error": None | "<message>"
            }
    """

    client = get_atlan_client()

    if display_name:
        logger.info(f"Retrieving Atlan tag with displayName='{display_name}'")
    else:
        logger.info("Retrieving ALL existing Atlan tags (no displayName provided).")

    try:
        response = client.typedef.get(type_category=AtlanTypeCategory.CLASSIFICATION)
        all_tag_defs: List[AtlanTagDef] = getattr(response, "atlan_tag_defs", []) or []

        logger.debug(f"Retrieved {len(all_tag_defs)} tag definitions from typedefs.")

        # If searching for a specific displayName
        if display_name:
            matches = [
                tag_def for tag_def in all_tag_defs
                if getattr(tag_def, "display_name", None) == display_name
            ]

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

        # Otherwise return ALL tags
        return {
            "tags": [
                {
                    "display_name": t.display_name,
                    "internal_name": getattr(t, "name", None),
                    "guid": getattr(t, "guid", None),
                    "description": getattr(t, "description", None),
                    "options": getattr(t, "options", {}) or {},
                }
                for t in all_tag_defs
            ],
            "count": len(all_tag_defs),
            "error": None,
        }

    except Exception as e:
        logger.error(
            "Error retrieving Atlan tag definitions: %s", e, exc_info=True
        )
        return {"tags": [], "count": 0, "error": str(e)}


# -------------------------------------------------------------------------
#  create_tag  (updated to use retrieve_tag_by_name)
# -------------------------------------------------------------------------
def create_tag(
    name: str,
    color: Optional[str] = None,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    image_url: Optional[str] = None,
    skip_display_name_uniqueness_check: bool = False,
) -> Dict[str, Any]:
    """
    Create a new Atlan tag definition, unless a tag with the same
    displayName already exists.

    Args:
        name (str): Human-readable display name of the tag.
        color (str, optional): Defaults to BLACK.
        description (str, optional)
        icon (str, optional)
        image_url (str, optional)
        skip_display_name_uniqueness_check (bool)

    Returns:
        Dict[str, Any]:
            - existing tag info if tag already exists
            - created tag info if created
            - error dict if failure
    """

    logger.info(
        f"Create-or-skip Atlan tag request: displayName={name}, "
        f"color={color or 'BLACK (default)'}, description={bool(description)}, "
        f"icon={bool(icon)}, image_url={bool(image_url)}, "
        f"skip_display_name_uniqueness_check={skip_display_name_uniqueness_check}"
    )

    client = get_atlan_client()

    # ------------------------------------------------------------------
    # 1. Check if tag already exists by displayName
    # ------------------------------------------------------------------
    result = retrieve_tag_by_name(name)

    if result["error"]:
        # propagate retrieval error
        return {"error": result["error"]}

    if result["count"] > 0:
        # Tag already exists — return that info
        existing = result["tags"][0]

        logger.info(
            f"Tag '{name}' already exists (internal={existing['internal_name']}, "
            f"guid={existing['guid']}) — skipping creation."
        )

        return {
            "exists": True,
            "created": False,
            "tag": existing,
            "message": "Tag already exists — skipping creation.",
        }

    # ------------------------------------------------------------------
    # 2. Determine color enum (optional)
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
    # 3. Build AtlanTagDef object
    # ------------------------------------------------------------------
    try:
        tag_def = AtlanTagDef.create(
            name=name,
            color=atlan_color_enum,
        )

        if description:
            tag_def.description = description
        if icon:
            tag_def.icon = icon
        if image_url:
            tag_def.image_url = image_url
        if skip_display_name_uniqueness_check:
            tag_def.skip_display_name_uniqueness_check = True

        logger.debug(f"Constructed AtlanTagDef for creation: {tag_def}")

    except Exception as e:
        logger.error(
            f"Failed to construct AtlanTagDef for displayName={name}: {e}",
            exc_info=True,
        )
        return {"error": str(e)}

    # ------------------------------------------------------------------
    # 4. Create tag through Atlan typedef API
    # ------------------------------------------------------------------
    try:
        response = client.typedef.create(tag_def)
        created_def = response[0] if response else None

        logger.info(
            f"Successfully created Atlan tag '{name}' "
            f"(internal={getattr(created_def, 'name', None)}, "
            f"guid={getattr(created_def, 'guid', None)})"
        )

        return {
            "exists": False,
            "created": True,
            "tag": {
                "display_name": created_def.display_name if created_def else name,
                "internal_name": getattr(created_def, "name", None),
                "guid": getattr(created_def, "guid", None),
                "color": atlan_color_enum.name,
                "description": description,
                "icon": icon,
                "image_url": image_url,
                "options": getattr(created_def, "options", {}) if created_def else {},
            },
        }

    except Exception as e:
        logger.error(
            f"Error creating Atlan tag '{name}': {e}", exc_info=True
        )
        return {"error": str(e)}

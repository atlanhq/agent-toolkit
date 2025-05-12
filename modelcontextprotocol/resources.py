import logging

from client import get_atlan_client
from pyatlan.model.enums import AtlanTypeCategory


logger = logging.getLogger(__name__)


def get_entity_typedefs() -> dict:
    """
    Get the entity typedefs from the Atlan client.

    Returns:
        dict: Dictionary containing entity typedefs.
    """
    try:
        client = get_atlan_client()
        typedefs = client.typedef.get(type_category=AtlanTypeCategory.ENTITY)
        response = []

        for entity_def in typedefs.entity_defs:
            attributes = []
            for attribute_def in entity_def.attribute_defs:
                attributes.append(
                    {
                        "name": attribute_def["name"],
                        "description": attribute_def.get("description", None),
                        "type": attribute_def.get("typeName", None),
                    }
                )
            response.append(
                {
                    "attribute_defs": attributes,
                    "name": entity_def.name,
                    "description": entity_def.description,
                    "sub_types": entity_def.sub_types,
                }
            )

        return {
            "status": "success",
            "entity_defs": response,
        }
    except Exception as e:
        logger.error(f"Error fetching entity typedefs: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "entity_defs": [],
        }


def get_tags() -> dict:
    """
    Get tags available in Atlan.

    Returns:
        dict: Dictionary containing tags.
    """
    try:
        client = get_atlan_client()
        typedefs = client.typedef.get(
            type_category=AtlanTypeCategory.CLASSIFICATION,
        )

        response = []
        for tag_def in typedefs.atlan_tag_defs:
            attributes = []
            for attribute_def in tag_def.attribute_defs:
                attributes.append(
                    {
                        "name": attribute_def.name,
                        "display_name": attribute_def.display_name,
                        "description": attribute_def.description,
                        "type": attribute_def.type_name,
                    }
                )
            response.append(
                {
                    "name": tag_def.name,
                    "display_name": tag_def.display_name,
                    "description": tag_def.description,
                    "attributes": attributes,
                }
            )

        return {
            "status": "success",
            "tags": response,
        }
    except Exception as e:
        logger.error(f"Error fetching classification typedefs: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "tags": [],
        }

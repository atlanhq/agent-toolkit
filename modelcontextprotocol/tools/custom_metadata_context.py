import logging
from typing import Any, Dict, List
from client import get_atlan_client
from pyatlan.cache.custom_metadata_cache import CustomMetadataCache
from pyatlan.cache.enum_cache import EnumCache

logger = logging.getLogger(__name__)


def process_business_metadata(
    cm_def: Any,
    enum_cache: EnumCache,
) -> Dict[str, Any]:
    """
    Generates context prompt for a given Atlan business metadata definition.

    Args:
        cm_def: CustomMetadataDef object from PyAtlan
        enum_cache: EnumCache instance for enriching enum attributes

    Returns:
        Dictionary containing prompt, metadata details, and id
    """
    cm_name = cm_def.name or "N/A"
    cm_display_name = cm_def.display_name or "N/A"
    description = cm_def.description or "No description available."
    guid = cm_def.guid

    # For prompt: comma separated attribute names and descriptions
    attributes_list_for_prompt: List[str] = []
    parsed_attributes_for_metadata: List[Dict[str, Any]] = []

    if cm_def.attribute_defs:
        for attr_def in cm_def.attribute_defs:
            attr_name = attr_def.display_name or attr_def.name or "Unnamed attribute"
            attr_desc = attr_def.description or "No description"
            attributes_list_for_prompt.append(f"{attr_name}:{attr_desc}")

            base_description = attr_def.description or ""
            enhanced_description = base_description

            # Check if attribute is an enum type and enrich with enum values
            if attr_def.options and attr_def.options.is_enum:
                enum_type = attr_def.options.enum_type
                if enum_type:
                    try:
                        enum_def = enum_cache.get_by_name(enum_type)
                        if enum_def and enum_def.element_defs:
                            enum_values = [elem.value for elem in enum_def.element_defs if elem.value]
                            if enum_values:
                                quoted_values = ", ".join([f"'{value}'" for value in enum_values])
                                enum_suffix = f" This attribute can have enum values: {quoted_values}."
                                enhanced_description = f"{base_description}{enum_suffix}".strip()

                            # Create enum enrichment data
                            enum_enrichment = {
                                "status": "ENRICHED",
                                "enumType": enum_type,
                                "enumGuid": enum_def.guid,
                                "enumDescription": enum_def.description,
                                "values": enum_values,
                            }
                    except Exception as e:
                        logger.debug(f"Could not enrich enum type {enum_type}: {e}")
                        enum_enrichment = None
                else:
                    enum_enrichment = None
            else:
                enum_enrichment = None

            attribute_metadata = {
                "name": attr_def.name,
                "display_name": attr_def.display_name,
                "data_type": attr_def.type_name,
                "description": enhanced_description,
            }

            if enum_enrichment:
                attribute_metadata["enumEnrichment"] = enum_enrichment

            parsed_attributes_for_metadata.append(attribute_metadata)

    attributes_str_for_prompt = (
        ", ".join(attributes_list_for_prompt) if attributes_list_for_prompt else "None"
    )

    metadata: Dict[str, Any] = {
        "name": cm_name,
        "display_name": cm_display_name,
        "description": description,
        "attributes": parsed_attributes_for_metadata,
    }

    prompt = f"""{cm_display_name}|{description}|{attributes_str_for_prompt}"""

    return {"prompt": prompt, "metadata": metadata, "id": guid}


def get_custom_metadata_context() -> Dict[str, Any]:
    """
    Fetch custom metadata context using PyAtlan's native cache classes.

    Returns:
        Dictionary containing context and business metadata results
    """
    business_metadata_results: List[Dict[str, Any]] = []

    try:
        # Get Atlan client
        client = get_atlan_client()

        # Initialize caches using PyAtlan's native classes
        cm_cache = CustomMetadataCache(client)
        enum_cache = EnumCache(client)

        # Get all custom metadata attributes (includes full definitions)
        all_custom_attributes = cm_cache.get_all_custom_attributes(
            include_deleted=False,
            force_refresh=True
        )

        # Process each custom metadata set
        for set_name in all_custom_attributes.keys():
            try:
                # Get the full custom metadata definition
                cm_def = cm_cache.get_custom_metadata_def(set_name)

                # Process and enrich with enum data
                result = process_business_metadata(cm_def, enum_cache)
                business_metadata_results.append(result)

            except Exception as e:
                logger.warning(
                    f"Error processing custom metadata set '{set_name}': {e}"
                )
                continue

        logger.info(
            f"Fetched {len(business_metadata_results)} business metadata definitions with enum enrichment."
        )

    except Exception as e:
        logger.error(
            f"Error fetching custom metadata context: {e}",
            exc_info=True,
        )
        return {
            "context": "Error fetching business metadata definitions",
            "business_metadata_results": [],
            "error": str(e)
        }

    return {
        "context": "This is the list of business metadata definitions used in the data catalog to add more information to an asset",
        "business_metadata_results": business_metadata_results,
    }

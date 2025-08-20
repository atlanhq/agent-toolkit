import logging
from typing import Any, Dict, List, Optional
from settings import Settings

logger = logging.getLogger(__name__)


def process_business_metadata(
    bm_def: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generates context prompt for a given Atlan business metadata definition.

    Args:
        bm_def: A dictionary representing the business metadata definition.
                Expected keys: 'displayName', 'description', 'attributeDefs'.

    Returns:
        A list containing a single string: the formatted semantic search prompt,
        and a list containing the metadata dictionary.
    """
    bm_def_name_for_prompt = bm_def.get("name", "N/A")
    bm_def_display_name = bm_def.get("displayName", "N/A")
    description_for_prompt = bm_def.get("description", "No description available.")

    attribute_defs = bm_def.get("attributeDefs", [])
    guid = bm_def.get("guid")

    # For prompt: comma separated attribute names and descriptions
    attributes_list_for_prompt: List[str] = []
    if attribute_defs:
        for attr in attribute_defs:
            attr_name = attr.get("displayName", attr.get("name", "Unnamed attribute"))
            attr_desc = attr.get(
                "description", "No description"
            )  # As per schema: names and descriptions
            attributes_list_for_prompt.append(f"{str(attr_name)}:{str(attr_desc)}")
    attributes_str_for_prompt = (
        ", ".join(attributes_list_for_prompt) if attributes_list_for_prompt else "None"
    )

    # For metadata: list of attribute objects
    parsed_attributes_for_metadata: List[Dict[str, Any]] = []
    if attribute_defs:
        for attr_def_item in attribute_defs:
            base_description = attr_def_item.get("description", "")
            
            # Check for enum enrichment and enhance description
            enum_enrichment = attr_def_item.get("enumEnrichment")
            enhanced_description = base_description
            if enum_enrichment and enum_enrichment.get("values"):
                enum_values = enum_enrichment["values"]
                if enum_values:
                    # Create comma-separated quoted values
                    quoted_values = ", ".join([f"'{value}'" for value in enum_values])
                    enum_suffix = f" This attribute can have enum values: {quoted_values}."
                    enhanced_description = f"{base_description}{enum_suffix}".strip()
            
            attribute_metadata = {
                "name": attr_def_item.get("name"),
                "display_name": attr_def_item.get("displayName"),
                "data_type": attr_def_item.get(
                    "typeName"
                ),  # Assuming typeName is data_type
                "description": enhanced_description,
            }

            # Include enum enrichment data if present
            if enum_enrichment:
                attribute_metadata["enumEnrichment"] = enum_enrichment

            parsed_attributes_for_metadata.append(attribute_metadata)

    metadata: Dict[str, Any] = {
        "name": bm_def_name_for_prompt,
        "display_name": bm_def_display_name,
        "description": description_for_prompt,
        "attributes": parsed_attributes_for_metadata,
    }

    prompt = f"""{bm_def_display_name}|{description_for_prompt}|{attributes_str_for_prompt}

This is a business metadata used in the data catalog to add more information to an asset"""

    return {"prompt": prompt, "metadata": metadata, "id": guid}


def get_custom_metadata_context() -> Dict[str, Any]:
    display_name: str = "Business Metadata"
    business_metadata_results: List[Dict[str, Any]] = []

    try:
        # Fetch enum definitions for enrichment
        enum_endpoint: str = Settings.get_atlan_typedef_api_endpoint(param="ENUM")
        enum_response: Optional[Dict[str, Any]] = Settings.make_request(enum_endpoint)
        enum_lookup: Dict[str, Dict[str, Any]] = {}
        if enum_response:
            enum_defs = enum_response.get("enumDefs", [])
            for enum_def in enum_defs:
                enum_name = enum_def.get("name", "")
                if enum_name:
                    enum_lookup[enum_name] = {
                        "guid": enum_def.get("guid", ""),
                        "description": enum_def.get("description", ""),
                        "values": [
                            element.get("value", "")
                            for element in enum_def.get("elementDefs", [])
                        ],
                        "elementDefs": enum_def.get("elementDefs", []),
                        "version": enum_def.get("version", 1),
                        "createTime": enum_def.get("createTime", 0),
                        "updateTime": enum_def.get("updateTime", 0),
                    }

        # Fetch business metadata definitions
        business_metadata_endpoint: str = Settings.get_atlan_typedef_api_endpoint(param="BUSINESS_METADATA")
        business_metadata_response: Optional[Dict[str, Any]] = Settings.make_request(business_metadata_endpoint)
        if business_metadata_response is None:
            logger.error(
                f"Service: Failed to make request to {business_metadata_endpoint} for {display_name}. No data returned."
            )
            return []
        
        business_metadata_defs: List[Dict[str, Any]] = business_metadata_response.get("businessMetadataDefs", [])

        # Enrich business metadata with enum information before processing
        for business_metadata_def in business_metadata_defs:
            # Enrich each business metadata definition with enum data
            attribute_defs = business_metadata_def.get("attributeDefs", [])
            for attribute in attribute_defs:
                options = attribute.get("options", {})
                is_enum = options.get("isEnum") == "true"

                if is_enum:
                    enum_type = options.get("enumType", "")
                    if enum_type and enum_type in enum_lookup:
                        enum_def = enum_lookup[enum_type]
                        attribute["enumEnrichment"] = {
                            "status": "ENRICHED",
                            "enumType": enum_type,
                            "enumGuid": enum_def["guid"],
                            "enumDescription": enum_def["description"],
                            "enumVersion": enum_def["version"],
                            "values": enum_def["values"],
                            "elementDefs": enum_def["elementDefs"],
                            "enrichedTimestamp": None,
                        }

            # Process the enriched business metadata
            business_metadata_results.append(process_business_metadata(business_metadata_def))

    except Exception as e:
        logger.error(
            f"Service: Error fetching or processing {display_name}: {e}",
            exc_info=True,
        )
        return []
    
    logger.info(
        f"Fetched {len(business_metadata_results)} {display_name} definitions with enum enrichment."
    )
    return business_metadata_results
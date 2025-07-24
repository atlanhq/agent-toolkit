import argparse
import json
from typing import List, Union, Any
from fastmcp import FastMCP
from tools import (
    search_assets,
    get_assets_by_dsl,
    traverse_lineage,
    update_assets,
    create_glossary_category_assets,
    create_glossary_assets,
    create_glossary_term_assets,
    UpdatableAttribute,
    CertificateStatus,
    UpdatableAsset,
    GlossarySpecification,
    GlossaryCategorySpecification,
    GlossaryTermSpecification,
)
from pyatlan.model.lineage import LineageDirection
from utils.parameters import (
    parse_json_parameter,
    parse_list_parameter,
)

mcp = FastMCP("Atlan MCP Server", dependencies=["pyatlan", "fastmcp"])


@mcp.tool()
def search_assets_tool(
    conditions=None,
    negative_conditions=None,
    some_conditions=None,
    min_somes=1,
    include_attributes=None,
    asset_type=None,
    include_archived=False,
    limit=10,
    offset=0,
    sort_by=None,
    sort_order="ASC",
    connection_qualified_name=None,
    tags=None,
    directly_tagged=True,
    domain_guids=None,
    date_range=None,
    guids=None,
):
    """
    Advanced asset search using FluentSearch with flexible conditions.

    Args:
        conditions (Dict[str, Any], optional): Dictionary of attribute conditions to match.
            Format: {"attribute_name": value} or {"attribute_name": {"operator": operator, "value": value}}
        negative_conditions (Dict[str, Any], optional): Dictionary of attribute conditions to exclude.
            Format: {"attribute_name": value} or {"attribute_name": {"operator": operator, "value": value}}
        some_conditions (Dict[str, Any], optional): Conditions for where_some() queries that require min_somes of them to match.
            Format: {"attribute_name": value} or {"attribute_name": {"operator": operator, "value": value}}
        min_somes (int): Minimum number of some_conditions that must match. Defaults to 1.
        include_attributes (List[Union[str, AtlanField]], optional): List of specific attributes to include in results.
            Can be string attribute names or AtlanField objects.
        asset_type (Union[Type[Asset], str], optional): Type of asset to search for.
            Either a class (e.g., Table, Column) or a string type name (e.g., "Table", "Column")
        include_archived (bool): Whether to include archived assets. Defaults to False.
        limit (int, optional): Maximum number of results to return. Defaults to 10.
        offset (int, optional): Offset for pagination. Defaults to 0.
        sort_by (str, optional): Attribute to sort by. Defaults to None.
        sort_order (str, optional): Sort order, "ASC" or "DESC". Defaults to "ASC".
        connection_qualified_name (str, optional): Connection qualified name to filter by.
        tags (List[str], optional): List of tags to filter by.
        directly_tagged (bool): Whether to filter for directly tagged assets only. Defaults to True.
        domain_guids (List[str], optional): List of domain GUIDs to filter by.
        date_range (Dict[str, Dict[str, Any]], optional): Date range filters.
            Format: {"attribute_name": {"gte": start_timestamp, "lte": end_timestamp}}
        guids (List[str], optional): List of asset GUIDs to filter by.

    Returns:
        List[Asset]: List of assets matching the search criteria

    Raises:
        Exception: If there's an error executing the search

    Examples:
        # Search for verified tables
        tables = search_assets(
            asset_type="Table",
            conditions={"certificate_status": CertificateStatus.VERIFIED.value}
        )

        # Search for assets missing descriptions
        missing_desc = search_assets(
            negative_conditions={
                "description": "has_any_value",
                "user_description": "has_any_value"
            },
            include_attributes=["owner_users", "owner_groups"]
        )

        # Search for columns with specific certificate status
        columns = search_assets(
            asset_type="Column",
            some_conditions={
                "certificate_status": [CertificateStatus.DRAFT.value, CertificateStatus.VERIFIED.value]
            },
            tags=["PRD"],
            conditions={"created_by": "username"},
            date_range={"create_time": {"gte": 1641034800000, "lte": 1672570800000}}
        )
        # Search for assets with a specific search text
        assets = search_assets(
            conditions = {
                "name": {
                    "operator": "match",
                    "value": "search_text"
                },
                "description": {
                    "operator": "match",
                    "value": "search_text"
                }
            }
        )


        # Search for assets using advanced operators
        assets = search_assets(
            conditions={
                "name": {
                    "operator": "startswith",
                    "value": "prefix_",
                    "case_insensitive": True
                },
                "description": {
                    "operator": "contains",
                    "value": "important data",
                    "case_insensitive": True
                },
                "create_time": {
                    "operator": "between",
                    "value": [1640995200000, 1643673600000]
                }
            }
        )

        # Search for assets with multiple type names (OR logic)
        assets = search_assets(
            conditions={
                "type_name": ["Table", "Column", "View"]  # Uses .within() for OR logic
            }
        )

        # Search for assets with compliant business policy
        assets = search_assets(
            conditions={
                "asset_policy_guids": "business_policy_guid"
            },
            include_attributes=["asset_policy_guids"]
        )

        # Search for assets with non compliant business policy
        assets = search_assets(
            conditions={
                "non_compliant_asset_policy_guids": "business_policy_guid"
            },
            include_attributes=["non_compliant_asset_policy_guids"]
        )

        # get non compliant business policies for an asset
         assets = search_assets(
            conditions={
                "name": "has_any_value",
                "displayName": "has_any_value",
                "guid": "has_any_value"
            },
            include_attributes=["non_compliant_asset_policy_guids"]
        )

        # get compliant business policies for an asset
         assets = search_assets(
            conditions={
                "name": "has_any_value",
                "displayName": "has_any_value",
                "guid": "has_any_value"
            },
            include_attributes=["asset_policy_guids"]
        )

        # get incident for a business policy
         assets = search_assets(
            conditions={
                "asset_type": "BusinessPolicyIncident",
                "business_policy_incident_related_policy_guids": "business_policy_guid"
            },
            some_conditions={
                "certificate_status": [CertificateStatus.DRAFT.value, CertificateStatus.VERIFIED.value]
            }
        )

        # Search for glossary terms by name and status
        glossary_terms = search_assets(
            asset_type="AtlasGlossaryTerm",
            conditions={
                "certificate_status": CertificateStatus.VERIFIED.value,
                "name": {
                    "operator": "contains",
                    "value": "customer",
                    "case_insensitive": True
                }
            },
            include_attributes=["categories"]
        )

    Additional attributes you can include in the conditions to extract more metadata from an asset:
        - columns
        - column_count
        - row_count
        - readme
        - owner_users
    """
    try:
        # Parse JSON string parameters if needed
        conditions = parse_json_parameter(conditions)
        negative_conditions = parse_json_parameter(negative_conditions)
        some_conditions = parse_json_parameter(some_conditions)
        date_range = parse_json_parameter(date_range)
        include_attributes = parse_list_parameter(include_attributes)
        tags = parse_list_parameter(tags)
        domain_guids = parse_list_parameter(domain_guids)
        guids = parse_list_parameter(guids)

        return search_assets(
            conditions,
            negative_conditions,
            some_conditions,
            min_somes,
            include_attributes,
            asset_type,
            include_archived,
            limit,
            offset,
            sort_by,
            sort_order,
            connection_qualified_name,
            tags,
            directly_tagged,
            domain_guids,
            date_range,
            guids,
        )
    except (json.JSONDecodeError, ValueError) as e:
        return {"error": f"Parameter parsing error: {str(e)}"}


@mcp.tool()
def get_assets_by_dsl_tool(dsl_query):
    """
    Execute the search with the given query
    dsl_query : Union[str, Dict[str, Any]] (required):
        The DSL query used to search the index.

    Example:
    dsl_query = '''{
    "query": {
        "function_score": {
            "boost_mode": "sum",
            "functions": [
                {"filter": {"match": {"starredBy": "john.doe"}}, "weight": 10},
                {"filter": {"match": {"certificateStatus": "VERIFIED"}}, "weight": 15},
                {"filter": {"match": {"certificateStatus": "DRAFT"}}, "weight": 10},
                {"filter": {"bool": {"must_not": [{"exists": {"field": "certificateStatus"}}]}}, "weight": 8},
                {"filter": {"bool": {"must_not": [{"terms": {"__typeName.keyword": ["Process", "DbtProcess"]}}]}}, "weight": 20}
            ],
            "query": {
                "bool": {
                    "filter": [
                        {
                            "bool": {
                                "minimum_should_match": 1,
                                "must": [
                                    {"bool": {"should": [{"terms": {"certificateStatus": ["VERIFIED"]}}]}},
                                    {"term": {"__state": "ACTIVE"}}
                                ],
                                "must_not": [
                                    {"term": {"isPartial": "true"}},
                                    {"terms": {"__typeName.keyword": ["Procedure", "DbtColumnProcess", "BIProcess", "MatillionComponent", "SnowflakeTag", "DbtTag", "BigqueryTag", "AIApplication", "AIModel"]}},
                                    {"terms": {"__typeName.keyword": ["MCIncident", "AnomaloCheck"]}}
                                ],
                                "should": [
                                    {"terms": {"__typeName.keyword": ["Query", "Collection", "AtlasGlossary", "AtlasGlossaryCategory", "AtlasGlossaryTerm", "Connection", "File"]}},
                                ]
                            }
                        }
                    ]
                },
                "score_mode": "sum"
            },
            "score_mode": "sum"
        }
    },
    "post_filter": {
        "bool": {
            "filter": [
                {
                    "bool": {
                        "must": [{"terms": {"__typeName.keyword": ["Table", "Column"]}}],
                        "must_not": [{"exists": {"field": "termType"}}]
                    }
                }
            ]
        },
        "sort": [
            {"_score": {"order": "desc"}},
            {"popularityScore": {"order": "desc"}},
            {"starredCount": {"order": "desc"}},
            {"name.keyword": {"order": "asc"}}
        ],
        "track_total_hits": true,
        "size": 10,
        "include_meta": false
    }'''
    response = get_assets_by_dsl(dsl_query)
    """
    return get_assets_by_dsl(dsl_query)


@mcp.tool()
def traverse_lineage_tool(
    guid,
    direction,
    depth=1000000,
    size=10,
    immediate_neighbors=True,
):
    """
    Traverse asset lineage in specified direction.

    Args:
        guid (str): GUID of the starting asset
        direction (str): Direction to traverse ("UPSTREAM" or "DOWNSTREAM")
        depth (int, optional): Maximum depth to traverse. Defaults to 1000000.
        size (int, optional): Maximum number of results to return. Defaults to 10.
        immediate_neighbors (bool, optional): Only return immediate neighbors. Defaults to True.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - assets: List of assets in the lineage
            - references: List of dictionaries containing:
                - source_guid: GUID of the source asset
                - target_guid: GUID of the target asset
                - direction: Direction of the reference (upstream/downstream)

    Example:
        # Get lineage with specific depth and size
        lineage = traverse_lineage_tool(
            guid="asset-guid-here",
            direction="DOWNSTREAM",
            depth=1000000,
            size=10
        )

        # Access assets and their references
        for asset in lineage["assets"]:
            print(f"Asset: {asset.guid}")

        for ref in lineage["references"]:
            print(f"Reference: {ref['source_guid']} -> {ref['target_guid']}")
    """
    try:
        direction_enum = LineageDirection[direction.upper()]
    except KeyError:
        raise ValueError(
            f"Invalid direction: {direction}. Must be either 'UPSTREAM' or 'DOWNSTREAM'"
        )

    return traverse_lineage(
        guid=guid,
        direction=direction_enum,
        depth=depth,
        size=size,
        immediate_neighbors=immediate_neighbors,
    )


@mcp.tool()
def update_assets_tool(
    assets,
    attribute_name,
    attribute_values,
):
    """
    Update one or multiple assets with different values for the same attribute.

    Args:
        assets (Union[Dict[str, Any], List[Dict[str, Any]]]): Asset(s) to update.
            Can be a single UpdatableAsset or a list of UpdatableAsset objects.
        attribute_name (str): Name of the attribute to update.
            Only "user_description", "certificate_status" and "readme" are supported.
        attribute_values (List[str]): List of values to set for the attribute.
            For certificateStatus, only "VERIFIED", "DRAFT", or "DEPRECATED" are allowed.
            For readme, the value must be a valid Markdown string.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - updated_count: Number of assets successfully updated
            - errors: List of any errors encountered

    Examples:
        # Update certificate status for a single asset
        result = update_assets_tool(
            assets={
                "guid": "asset-guid-here",
                "name": "Asset Name",
                "type_name": "Asset Type Name",
                "qualified_name": "Asset Qualified Name"
            },
            attribute_name="certificate_status",
            attribute_values=["VERIFIED"]
        )

        # Update user description for multiple assets
        result = update_assets_tool(
            assets=[
                {
                    "guid": "asset-guid-1",
                    "name": "Asset Name 1",
                    "type_name": "Asset Type Name 1",
                    "qualified_name": "Asset Qualified Name 1"
                },
                {
                    "guid": "asset-guid-2",
                    "name": "Asset Name 2",
                    "type_name": "Asset Type Name 2",
                    "qualified_name": "Asset Qualified Name 2"
                }
            ],
            attribute_name="user_description",
            attribute_values=[
                "New description for asset 1", "New description for asset 2"
            ]
        )

        # Update readme for a single asset with Markdown
        result = update_assets_tool(
            assets={
                "guid": "asset-guid-here",
                "name": "Asset Name",
                "type_name": "Asset Type Name",
                "qualified_name": "Asset Qualified Name"
            },
            attribute_name="readme",
            attribute_values=['''# Customer Data Table
            Contains customer transaction records for analytics.
            **Key Info:**
            - Updated daily at 2 AM
            - Contains PII data
            - [Documentation](https://docs.example.com)''']
        )
    """
    try:
        # Parse JSON parameters
        parsed_assets = parse_json_parameter(assets)
        parsed_attribute_values = parse_list_parameter(attribute_values)

        # Convert string attribute name to enum
        attr_enum = UpdatableAttribute(attribute_name)

        # For certificate status, convert values to enum
        if attr_enum == UpdatableAttribute.CERTIFICATE_STATUS:
            parsed_attribute_values = [
                CertificateStatus(val) for val in parsed_attribute_values
            ]

        # Convert assets to UpdatableAsset objects
        if isinstance(parsed_assets, dict):
            updatable_assets = [UpdatableAsset(**parsed_assets)]
        else:
            updatable_assets = [UpdatableAsset(**asset) for asset in parsed_assets]

        return update_assets(
            updatable_assets=updatable_assets,
            attribute_name=attr_enum,
            attribute_values=parsed_attribute_values,
        )
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        return {
            "error": f"Parameter parsing/conversion error: {str(e)}",
            "updated_count": 0,
        }


@mcp.tool()
def create_glossary_assets_tool(
    glossaries: Union[str, dict, List[Union[dict, GlossarySpecification]]],
) -> dict[str, Any]:
    """
    Create one or multiple AtlasGlossary assets in Atlan.

    Args:
        glossaries: Either a single glossary specification (dict) or a list of glossary specifications.
            Each specification can be a dictionary or GlossarySpecification object containing:
            - name (str): Name of the glossary (required)
            - description (str, optional): Short description of the glossary
            - long_description (str, optional): Detailed description of the glossary
            - certificate_status (str, optional): Certification status ("VERIFIED", "DRAFT", or "DEPRECATED")
            - asset_icon (str, optional): Icon for the glossary (e.g., "BOOK_OPEN_TEXT")
            - owner_users (List[str], optional): List of user names who should own this glossary
            - owner_groups (List[str], optional): List of group names who should own this glossary

    Returns:
        Dict[str, Any]: Dictionary containing:
            - results: List of dictionaries for each glossary creation attempt with details:
                - index: Index of the glossary in the input (0 for single glossary)
                - guid: The GUID of the created glossary (if successful)
                - name: The name of the glossary
                - qualified_name: The qualified name of the created glossary (if successful)
                - success: Boolean indicating if creation was successful
                - errors: List of any errors encountered for this specific glossary
            - successful_count: Number of glossaries created successfully
            - failed_count: Number of glossaries that failed to create
            - overall_success: Boolean indicating if all glossaries were created successfully
            - errors: List of overall errors (not specific to individual glossaries)
            - is_batch: Boolean indicating if this was a batch operation

    Examples:
        # Create a single glossary
        result = create_glossary_assets_tool({
            "name": "Business Terms",
            "description": "Common business terminology",
            "certificate_status": "VERIFIED"
        })

        # Create multiple glossaries
        result = create_glossary_assets_tool([
            {
                "name": "Business Terms",
                "description": "Common business terminology",
                "certificate_status": "VERIFIED"
            },
            {
                "name": "Technical Dictionary",
                "description": "Technical terminology and definitions",
                "certificate_status": "DRAFT"
            }
        ])
    """

    # Parse parameters to handle JSON strings using shared utility
    try:
        glossaries = parse_json_parameter(glossaries)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON format for glossaries parameter: {str(e)}"}

    return create_glossary_assets(glossaries)


@mcp.tool()
def create_glossary_term_assets_tool(
    terms: Union[str, dict, List[Union[dict, GlossaryTermSpecification]]],
) -> dict[str, Any]:
    """
    Create one or multiple AtlasGlossaryTerm assets in Atlan.

    Args:
        terms: Either a single term specification (dict) or a list of term specifications.
            Each specification can be a dictionary or GlossaryTermSpecification object containing:
            - name (str): Name of the term (required)
            - glossary_guid (str): GUID of the glossary this term belongs to (required)
            - alias (str, optional): An alias for the term
            - description (str, optional): Short description of the term
            - long_description (str, optional): Detailed description of the term
            - certificate_status (str, optional): Certification status ("VERIFIED", "DRAFT", or "DEPRECATED")
            - categories (List[str], optional): List of category GUIDs this term belongs to
            - owner_users (List[str], optional): List of user names who should own this term
            - owner_groups (List[str], optional): List of group names who should own this term

    Returns:
        Dict[str, Any]: Dictionary containing:
            - results: List of dictionaries for each term creation attempt with details:
                - index: Index of the term in the input (0 for single term)
                - guid: The GUID of the created term (if successful)
                - name: The name of the term
                - qualified_name: The qualified name of the created term (if successful)
                - glossary_guid: The GUID of the parent glossary
                - success: Boolean indicating if creation was successful
                - errors: List of any errors encountered for this specific term
            - successful_count: Number of terms created successfully
            - failed_count: Number of terms that failed to create
            - overall_success: Boolean indicating if all terms were created successfully
            - errors: List of overall errors (not specific to individual terms)
            - is_batch: Boolean indicating if this was a batch operation

    Examples:
        # Create a single term
        result = create_glossary_term_assets_tool({
            "name": "Customer",
            "glossary_guid": "glossary-guid-here",
            "description": "An individual or organization that purchases goods or services",
            "certificate_status": "VERIFIED"
        })

        # Create multiple terms
        result = create_glossary_term_assets_tool([
            {
                "name": "Customer",
                "glossary_guid": "glossary-guid-here",
                "description": "An individual or organization that purchases goods or services",
                "certificate_status": "VERIFIED"
            },
            {
                "name": "Annual Recurring Revenue",
                "glossary_guid": "glossary-guid-here",
                "description": "The yearly value of recurring revenue from customers",
                "certificate_status": "DRAFT",
                "categories": ["category-guid-1"],
                "owner_users": ["revenue.analyst"]
            }
        ])
    """
    # Parse parameters to handle JSON strings using shared utility
    try:
        terms = parse_json_parameter(terms)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON format for terms parameter: {str(e)}"}

    return create_glossary_term_assets(terms)


@mcp.tool()
def create_glossary_category_assets_tool(
    categories: Union[str, dict, List[Union[dict, GlossaryCategorySpecification]]],
) -> dict[str, Any]:
    """
    Create one or multiple AtlasGlossaryCategory assets in Atlan.

    Args:
        categories: Either a single category specification (dict) or a list of category specifications.
            Each specification can be a dictionary or GlossaryCategorySpecification object containing:
            - name (str): Name of the category (required)
            - glossary_guid (str): GUID of the glossary this category belongs to (required)
            - description (str, optional): Short description of the category
            - long_description (str, optional): Detailed description of the category
            - certificate_status (str, optional): Certification status ("VERIFIED", "DRAFT", or "DEPRECATED")
            - parent_category_guid (str, optional): GUID of the parent category if this is a subcategory
            - owner_users (List[str], optional): List of user names who should own this category
            - owner_groups (List[str], optional): List of group names who should own this category

    Returns:
        Dict[str, Any]: Dictionary containing:
            - results: List of dictionaries for each category creation attempt with details:
                - index: Index of the category in the input (0 for single category)
                - guid: The GUID of the created category (if successful)
                - name: The name of the category
                - qualified_name: The qualified name of the created category (if successful)
                - glossary_guid: The GUID of the parent glossary
                - success: Boolean indicating if creation was successful
                - errors: List of any errors encountered for this specific category
            - successful_count: Number of categories created successfully
            - failed_count: Number of categories that failed to create
            - overall_success: Boolean indicating if all categories were created successfully
            - errors: List of overall errors (not specific to individual categories)
            - is_batch: Boolean indicating if this was a batch operation

    Examples:
        # Create a single category
        result = create_glossary_category_assets_tool({
            "name": "Customer Data",
            "glossary_guid": "glossary-guid-here",
            "description": "Terms related to customer information and attributes",
            "certificate_status": "VERIFIED"
        })

        # Create multiple categories
        result = create_glossary_category_assets_tool([
            {
                "name": "Customer Data",
                "glossary_guid": "glossary-guid-here",
                "description": "Terms related to customer information and attributes",
                "certificate_status": "VERIFIED"
            },
            {
                "name": "Product Data",
                "glossary_guid": "glossary-guid-here",
                "description": "Terms related to product information and attributes",
                "certificate_status": "DRAFT",
                "owner_users": ["product.manager"]
            }
        ])
    """
    # Parse parameters to handle JSON strings using shared utility
    try:
        categories = parse_json_parameter(categories)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON format for categories parameter: {str(e)}"}

    return create_glossary_category_assets(categories)


def main():
    mcp.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Atlan MCP Server")
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio", "sse", "streamable-http"],
        help="Transport protocol (stdio/sse/streamable-http)",
    )
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to run the server on"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to run the server on"
    )
    parser.add_argument(
        "--path", type=str, default="/", help="Path of the streamable HTTP server"
    )
    args = parser.parse_args()

    kwargs = {"transport": args.transport}
    if args.transport == "streamable-http" or args.transport == "sse":
        kwargs = {
            "transport": args.transport,
            "host": args.host,
            "port": args.port,
            "path": args.path,
        }
    # Run the server with the specified transport and host/port/path
    mcp.run(**kwargs)

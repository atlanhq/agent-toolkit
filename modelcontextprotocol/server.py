import argparse
from fastmcp import FastMCP
from tools import (
    search_assets,
    get_assets_by_dsl,
    traverse_lineage,
    update_assets,
    create_glossary_asset,
    create_glossary_category_asset,
    create_glossary_term_asset,
    UpdatableAttribute,
    CertificateStatus,
    UpdatableAsset,
)
from pyatlan.model.lineage import LineageDirection

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

    """
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
        guid=str(guid),
        direction=direction_enum,
        depth=int(depth),
        size=int(size),
        immediate_neighbors=bool(immediate_neighbors),
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
            Only "user_description" and "certificate_status" are supported.
        attribute_values (List[str]): List of values to set for the attribute.
            For certificateStatus, only "VERIFIED", "DRAFT", or "DEPRECATED" are allowed.

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

    """
    try:
        # Convert string attribute name to enum
        attr_enum = UpdatableAttribute(attribute_name)

        # For certificate status, validate and convert values to enum
        if attr_enum == UpdatableAttribute.CERTIFICATE_STATUS:
            attribute_values = [CertificateStatus(val) for val in attribute_values]

        # Convert assets to UpdatableAsset objects
        if isinstance(assets, dict):
            updatable_assets = [UpdatableAsset(**assets)]
        elif isinstance(assets, list):
            updatable_assets = [UpdatableAsset(**asset) for asset in assets]
        else:
            raise ValueError("Assets must be a dictionary or a list of dictionaries")

        return update_assets(
            updatable_assets=updatable_assets,
            attribute_name=attr_enum,
            attribute_values=attribute_values,
        )
    except ValueError as e:
        return {"updated_count": 0, "errors": [str(e)]}


@mcp.tool()
def create_glossary_asset_tool(
    name,
    description=None,
    long_description=None,
    certificate_status=None,
    asset_icon=None,
    owner_users=None,
    owner_groups=None,
):
    """
    Create a new AtlasGlossary asset in Atlan.

    Args:
        name (str): Name of the glossary (required).
        description (str, optional): Short description of the glossary.
        long_description (str, optional): Detailed description of the glossary.
        certificate_status (str, optional): Certification status of the glossary.
            Can be "VERIFIED", "DRAFT", or "DEPRECATED".
        asset_icon (str, optional): Icon for the glossary. For example: "BOOK_OPEN_TEXT".
        owner_users (List[str], optional): List of user names who should own this glossary.
        owner_groups (List[str], optional): List of group names who should own this glossary.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - guid: The GUID of the created glossary
            - name: The name of the created glossary
            - qualified_name: The qualified name of the created glossary
            - success: Boolean indicating if creation was successful
            - errors: List of any errors encountered

    Examples:
        # Create a basic glossary
        result = create_glossary_asset_tool(
            name="Business Terms",
            description="Common business terminology used across the organization"
        )

        # Create a glossary with icon, certification, and ownership
        result = create_glossary_asset_tool(
            name="Data Quality Glossary",
            description="Terms related to data quality standards",
            long_description="This glossary contains comprehensive definitions of data quality metrics, standards, and processes used throughout our data platform.",
            certificate_status="VERIFIED",
            asset_icon="BOOK_OPEN_TEXT",
            owner_users=["john.doe", "jane.smith"],
            owner_groups=["data-stewards"]
        )

        # Create a minimal glossary with only a name
        result = create_glossary_asset_tool(
            name="Finance Glossary"
        )

        # Create a glossary marked as DRAFT with an owner
        result = create_glossary_asset_tool(
            name="Marketing Glossary",
            certificate_status="DRAFT",
            owner_users=["sally.marketing"]
        )
    """
    return create_glossary_asset(
        name=name,
        description=description,
        long_description=long_description,
        certificate_status=certificate_status,
        asset_icon=asset_icon,
        owner_users=owner_users,
        owner_groups=owner_groups,
    )


@mcp.tool()
def create_glossary_category_asset_tool(
    name,
    glossary_guid,
    description=None,
    long_description=None,
    certificate_status=None,
    parent_category_guid=None,
    owner_users=None,
    owner_groups=None,
):
    """
    Create a new AtlasGlossaryCategory asset in Atlan.

    Args:
        name (str): Name of the category (required).
        glossary_guid (str): GUID of the glossary this category belongs to (required).
        description (str, optional): Short description of the category.
        long_description (str, optional): Detailed description of the category.
        certificate_status (str, optional): Certification status of the category.
            Can be "VERIFIED", "DRAFT", or "DEPRECATED".
        parent_category_guid (str, optional): GUID of the parent category if this is a subcategory.
        owner_users (List[str], optional): List of user names who should own this category.
        owner_groups (List[str], optional): List of group names who should own this category.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - guid: The GUID of the created category
            - name: The name of the created category
            - qualified_name: The qualified name of the created category
            - glossary_guid: The GUID of the parent glossary
            - success: Boolean indicating if creation was successful
            - errors: List of any errors encountered

    Examples:
        # Create a basic category
        result = create_glossary_category_asset_tool(
            name="Customer Data",
            glossary_guid="glossary-guid-here",
            description="Terms related to customer information and attributes"
        )

        # Create a subcategory with detailed information and certification
        result = create_glossary_category_asset_tool(
            name="Customer Demographics",
            glossary_guid="glossary-guid-here",
            parent_category_guid="parent-category-guid-here",
            description="Terms specific to customer demographic information",
            long_description="This category contains terms that define various demographic attributes of customers such as age groups, income brackets, geographic regions, etc.",
            certificate_status="VERIFIED",
            owner_users=["data.steward"],
            owner_groups=["customer-analytics-team"]
        )

        # Create a category with a parent and owners
        result = create_glossary_category_asset_tool(
            name="Campaign Metrics",
            glossary_guid="marketing-glossary-guid",
            parent_category_guid="metrics-category-guid",
            owner_groups=["marketing-analytics"]
        )

        # Create a verified top-level category
        result = create_glossary_category_asset_tool(
            name="Financial Reporting",
            glossary_guid="finance-glossary-guid",
            certificate_status="VERIFIED"
        )
    """
    return create_glossary_category_asset(
        name=name,
        glossary_guid=glossary_guid,
        description=description,
        long_description=long_description,
        certificate_status=certificate_status,
        parent_category_guid=parent_category_guid,
        owner_users=owner_users,
        owner_groups=owner_groups,
    )


@mcp.tool()
def create_glossary_term_asset_tool(
    name,
    glossary_guid,
    alias=None,
    description=None,
    long_description=None,
    certificate_status=None,
    categories=None,
    owner_users=None,
    owner_groups=None,
):
    """
    Create a new AtlasGlossaryTerm asset in Atlan.

    Args:
        name (str): Name of the term (required).
        glossary_guid (str): GUID of the glossary this term belongs to (required).
        description (str, optional): Short description of the term.
        long_description (str, optional): Detailed description of the term.
        certificate_status (str, optional): Certification status of the term.
            Can be "VERIFIED", "DRAFT", or "DEPRECATED".
        categories (List[str], optional): List of category GUIDs this term belongs to.
        owner_users (List[str], optional): List of user names who should own this term.
        owner_groups (List[str], optional): List of group names who should own this term.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - guid: The GUID of the created term
            - name: The name of the created term
            - qualified_name: The qualified name of the created term
            - glossary_guid: The GUID of the parent glossary
            - success: Boolean indicating if creation was successful
            - errors: List of any errors encountered

    Examples:
        # Create a basic term
        result = create_glossary_term_asset_tool(
            name="Customer",
            glossary_guid="glossary-guid-here",
            description="An individual or organization that purchases goods or services"
        )

        # Create a comprehensive term with relationships and certification
        result = create_glossary_term_asset_tool(
            name="Annual Recurring Revenue",
            glossary_guid="glossary-guid-here",
            description="The yearly value of recurring revenue from customers",
            long_description="Annual Recurring Revenue (ARR) is a key metric that represents the yearly value of recurring revenue streams. It includes subscription fees and other predictable revenue sources, excluding one-time payments or variable fees.",
            certificate_status="VERIFIED",
            categories=["category-guid-1", "category-guid-2"],
            owner_users=["revenue.analyst"],
            owner_groups=["finance-team"]
        )

        # Create a deprecated term
        result = create_glossary_term_asset_tool(
            name="Old Revenue Metric",
            glossary_guid="finance-glossary-guid",
            certificate_status="DEPRECATED",
            description="This metric is no longer in use."
        )

        # Create a term assigned to a category with an alias
        result = create_glossary_term_asset_tool(
            name="Click-Through Rate",
            glossary_guid="marketing-glossary-guid",
            categories=["campaign-metrics-guid"]
        )
    """
    return create_glossary_term_asset(
        name=name,
        glossary_guid=glossary_guid,
        alias=alias,
        description=description,
        long_description=long_description,
        certificate_status=certificate_status,
        categories=categories,
        owner_users=owner_users,
        owner_groups=owner_groups,
    )


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

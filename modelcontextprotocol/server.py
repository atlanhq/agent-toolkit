from mcp.server.fastmcp import FastMCP
from tools import (
    search_assets,
    get_assets_by_dsl,
    traverse_lineage,
    update_assets,
    UpdatableAttribute,
    CertificateStatus,
    UpdatableAsset,
)
from pyatlan.model.lineage import LineageDirection

mcp = FastMCP("Atlan MCP", dependencies=["pyatlan"])


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

    ⚠️ IMPORTANT NOTES FOR AI AGENTS ⚠️
    
    1. ALL dictionary parameters (conditions, negative_conditions, some_conditions) MUST be passed as JSON strings:
       - Correct: '{"description": {"operator": "has_any_value"}}'
       - Incorrect: {"description": {"operator": "has_any_value"}}
    
    2. Common Operators Available:
       - Check if field has any value: {"field": {"operator": "has_any_value"}}
       - Exact match: {"field": "value"} or {"field": {"operator": "eq", "value": "value"}}
       - Pattern match: {"field": {"operator": "match", "value": "pattern"}}
       - Starts with: {"field": {"operator": "startswith", "value": "prefix"}}
    
    3. include_attributes MUST be a JSON array string:
       - Correct: '["name", "description", "qualified_name"]'
       - Incorrect: ["name", "description", "qualified_name"]
    
    4. Common Attributes Available:
       - Basic: "name", "description", "user_description", "qualified_name"
       - Status: "certificate_status", "announcement_title", "announcement_message"
       - Ownership: "owner_users", "owner_groups", "admin_users", "admin_groups"
    
    5. asset_type MUST be a string matching exactly (case-sensitive):
       - Common types: "Table", "Column", "View", "Schema", "Database"
    
    Examples:
    
    1. Search for tables with descriptions:
    ```python
    search_assets_tool(
        asset_type="Table",
        conditions='{"description": {"operator": "has_any_value"}}',
        include_attributes='["name", "description", "qualified_name"]'
    )
    ```

    2. Search for tables with descriptions and sort by popularity score:
    ```python
    search_assets_tool(
        asset_type="Table",
        conditions='{"description": {"operator": "has_any_value"}}',
        include_attributes='["name", "description", "qualified_name"]',
        sort_by="popularityScore",
        sort_order="DESC"
    )
    ```

    3. Search for verified tables:
    ```python
    search_assets_tool(
        asset_type="Table",
        conditions='{"certificate_status": "VERIFIED"}',
        include_attributes='["name", "qualified_name", "certificate_status"]'
    )
    ```

    4. Search for assets missing descriptions:
    ```python
    search_assets_tool(
        negative_conditions='{"description": {"operator": "has_any_value"}, "user_description": {"operator": "has_any_value"}}',
        include_attributes='["name", "owner_users", "owner_groups"]'
    )
    ```

    5. Search for columns with specific certificate status:
    ```python
    search_assets_tool(
        asset_type="Column",
        some_conditions='{"certificate_status": ["DRAFT", "VERIFIED"]}',
        tags='["PRD"]',
        conditions='{"created_by": "username"}',
        date_range='{"create_time": {"gte": 1641034800000, "lte": 1672570800000}}'
    )
    ```

    6. Search for assets with a specific search text:
    ```python
    search_assets_tool(
        conditions='{"name": {"operator": "match", "value": "search_text"}, "description": {"operator": "match", "value": "search_text"}}'
    )
    ```

    7. Search for assets with compliant business policy:
    ```python
    search_assets_tool(
        conditions='{"asset_policy_guids": "business_policy_guid"}',
        include_attributes='["asset_policy_guids"]'
    )
    ```

    Args:
        conditions (str): JSON string of attribute conditions to match.
            Format: '{"attribute": value}' or '{"attribute": {"operator": op, "value": val}}'
            
        negative_conditions (str): JSON string of attribute conditions to exclude.
            Same format as conditions.
            
        some_conditions (str): JSON string for where_some() queries.
            Same format as conditions.
            
        min_somes (int): Minimum number of some_conditions that must match. Defaults to 1.
        
        include_attributes (str): JSON array string of attributes to include.
            Example: '["name", "description", "qualified_name"]'
            
        asset_type (str): Type of asset to search for (e.g., "Table", "Column").
            Case sensitive, must match exactly.
            
        include_archived (bool): Whether to include archived assets. Defaults to False.
        limit (int): Maximum number of results to return. Defaults to 10.
        offset (int): Offset for pagination. Defaults to 0.
        sort_by (str): Attribute to sort by. Defaults to None.
        sort_order (str): Sort order, "ASC" or "DESC". Defaults to "ASC".
        connection_qualified_name (str): Connection qualified name to filter by.
        tags (List[str]): List of tags to filter by.
        directly_tagged (bool): Whether to filter for directly tagged assets only. Defaults to True.
        domain_guids (List[str]): List of domain GUIDs to filter by.
        date_range (Dict): Date range filters.
            Format: {"attribute": {"gte": start_timestamp, "lte": end_timestamp}}
        guids (List[str]): List of asset GUIDs to filter by.

    Returns:
        List[Asset]: List of assets matching the search criteria
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

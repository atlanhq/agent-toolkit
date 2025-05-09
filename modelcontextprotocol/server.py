from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from tools import (
    search_assets,
    get_assets_by_dsl,
    traverse_lineage,
    update_assets,
    create_custom_metadata,
    get_custom_metadata,
    update_custom_metadata,
    create_badge,
    update_badge,
    delete_badge,
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
def create_custom_metadata_tool(
    display_name: str,
    attributes: List[Dict[str, Any]],
    description: Optional[str] = None,
    emoji: Optional[str] = None,
    logo_url: Optional[str] = None,
    locked: bool = False,
):
    """
    Create a custom metadata definition in Atlan.

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
        Dict[str, Any]: Response containing:
            - created: Boolean indicating if creation was successful
            - guid: GUID of the created custom metadata definition
            - error: Error message if creation failed

    Examples:
        # Create RACI custom metadata with descriptions
        result = create_custom_metadata_tool(
            display_name="RACI",
            description="RACI matrix for data assets",
            attributes=[
                {
                    "display_name": "Responsible",
                    "attribute_type": "USERS",
                    "description": "Who is responsible for this asset",
                    "multi_valued": False
                },
                {
                    "display_name": "Accountable",
                    "attribute_type": "USERS",
                    "description": "Who is accountable for this asset",
                    "multi_valued": False
                },
                {
                    "display_name": "Consulted",
                    "attribute_type": "GROUPS",
                    "description": "Who should be consulted about this asset",
                    "multi_valued": True
                },
                {
                    "display_name": "Informed",
                    "attribute_type": "GROUPS",
                    "description": "Who should be informed about changes",
                    "multi_valued": True
                }
            ],
            emoji="👪",
            locked=False
        )

        # Create a custom metadata with descriptions and logo URL
        result = create_custom_metadata_tool(
            display_name="Data Quality",
            description="Data quality metrics and scores",
            attributes=[
                {
                    "display_name": "Score",
                    "attribute_type": "INTEGER",
                    "description": "Overall quality score (0-100)"
                },
                {
                    "display_name": "Last Check",
                    "attribute_type": "DATE",
                    "description": "When the quality was last assessed"
                },
                {
                    "display_name": "Status",
                    "attribute_type": "STRING",
                    "description": "Current quality status",
                    "options_name": "quality_status"
                }
            ],
            logo_url="https://example.com/quality-logo.png",
            locked=True
        )
    """
    return create_custom_metadata(
        display_name=display_name,
        attributes=attributes,
        description=description,
        emoji=emoji,
        logo_url=logo_url,
        locked=locked,
    )


@mcp.tool()
def get_custom_metadata_tool(name: str):
    """
    Retrieve an existing custom metadata definition.

    Args:
        name (str): Name of the custom metadata to retrieve

    Returns:
        Dict[str, Any]: Response containing:
            - found: Boolean indicating if metadata was found
            - metadata: Custom metadata definition if found
            - error: Error message if retrieval failed

    Example:
        # Get RACI metadata definition
        result = get_custom_metadata_tool(name="RACI")
        if result["found"]:
            metadata = result["metadata"]
            print(f"Found metadata with {len(metadata.attribute_defs)} attributes")
    """
    return get_custom_metadata(name)


@mcp.tool()
def update_custom_metadata_tool(
    name: str,
    add_attributes: Optional[List[Dict[str, Any]]] = None,
    modify_attributes: Optional[Dict[str, Dict[str, Any]]] = None,
    remove_attributes: Optional[List[str]] = None,
    archived_by: Optional[str] = None,
):
    """
    Update an existing custom metadata definition.

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

    Examples:
        # Add a new attribute to RACI
        result = update_custom_metadata_tool(
            name="RACI",
            add_attributes=[{
                "display_name": "Additional Info",
                "attribute_type": "STRING",
                "description": "Additional information"
            }]
        )

        # Modify an existing RACI attribute
        result = update_custom_metadata_tool(
            name="RACI",
            modify_attributes={
                "Additional Info": {
                    "display_name": "More Info",
                    "description": "Updated description"
                }
            }
        )

        # Remove attributes from RACI
        result = update_custom_metadata_tool(
            name="RACI",
            remove_attributes=["More Info"],
            archived_by="jsmith"
        )
    """
    return update_custom_metadata(
        name=name,
        add_attributes=add_attributes,
        modify_attributes=modify_attributes,
        remove_attributes=remove_attributes,
        archived_by=archived_by,
    )


@mcp.tool()
def create_badge_tool(
    name: str,
    metadata_name: str,
    attribute_name: str,
    display_name: Optional[str] = None,
    description: Optional[str] = None,
    emoji: Optional[str] = None,
    logo_url: Optional[str] = None,
    badge_conditions: Optional[List[Dict[str, Any]]] = None,
):
    """
    Create a badge for a custom metadata attribute with optional conditions.

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

    Examples:
        # Create a simple badge
        result = create_badge_tool(
            name="raci-responsible",
            metadata_name="RACI",
            attribute_name="Responsible",
            display_name="RACI Lead"
        )

        # Create a badge with conditions
        result = create_badge_tool(
            name="data-quality-score",
            metadata_name="Data Quality",
            attribute_name="Score",
            display_name="Quality Score",
            description="Data quality score",
            badge_conditions=[
                {
                    "operator": "GTE",
                    "value": "80",
                    "color": "GREEN"
                },
                {
                    "operator": "LT",
                    "value": "80",
                    "color": "YELLOW"
                }
            ]
        )
    """
    return create_badge(
        name=name,
        metadata_name=metadata_name,
        attribute_name=attribute_name,
        display_name=display_name,
        description=description,
        emoji=emoji,
        logo_url=logo_url,
        badge_conditions=badge_conditions,
    )


@mcp.tool()
def update_badge_tool(
    name: str,
    display_name: Optional[str] = None,
    description: Optional[str] = None,
    emoji: Optional[str] = None,
    logo_url: Optional[str] = None,
):
    """
    Update an existing badge definition.

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

    Example:
        # Update badge display name and emoji
        result = update_badge_tool(
            name="raci-responsible",
            display_name="RACI Lead",
            emoji="👨‍💼"
        )
    """
    return update_badge(
        name=name,
        display_name=display_name,
        description=description,
        emoji=emoji,
        logo_url=logo_url,
    )


@mcp.tool()
def delete_badge_tool(guid: str):
    """
    Delete a badge completely.

    Args:
        guid (str): GUID of the badge to delete

    Returns:
        Dict[str, Any]: Response containing:
            - deleted: Boolean indicating if deletion was successful
            - error: Error message if deletion failed

    Example:
        result = delete_badge_tool(guid="1c932bbb-fbe6-4bbc-9d0d-3df2f1fa4f81")
    """
    return delete_badge(guid=guid)

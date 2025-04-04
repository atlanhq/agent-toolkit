from fastmcp import FastMCP
from tools import search_assets, get_assets_by_dsl
from pyatlan.model.fields.atlan_fields import AtlanField
from typing import Optional, Dict, Any, List, Union, Type
from pyatlan.model.assets import Asset

mcp = FastMCP("Altan MCP", dependencies=["pyatlan"])


@mcp.tool()
def search_assets_tool(
    conditions: Optional[Union[Dict[str, Any], str]] = None,
    negative_conditions: Optional[Dict[str, Any]] = None,
    some_conditions: Optional[Dict[str, Any]] = None,
    min_somes: int = 1,
    include_attributes: Optional[List[Union[str, AtlanField]]] = None,
    asset_type: Optional[Union[Type[Asset], str]] = None,
    include_archived: bool = False,
    limit: int = 10,
    offset: int = 0,
    sort_by: Optional[str] = None,
    sort_order: str = "ASC",
    connection_qualified_name: Optional[str] = None,
    tags: Optional[List[str]] = None,
    directly_tagged: bool = True,
    domain_guids: Optional[List[str]] = None,
    date_range: Optional[Dict[str, Dict[str, Any]]] = None,
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
    )


@mcp.tool()
def get_assets_by_dsl_tool(dsl_query: str):
    """
    Execute the search with the given query
    dsl_query : str (required):
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

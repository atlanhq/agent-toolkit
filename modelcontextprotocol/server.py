import argparse
import json
import os
from typing import Any, Dict, List
from fastmcp import FastMCP
from tools import (
    search_assets,
    get_assets_by_dsl,
    traverse_lineage,
    update_assets,
    query_asset,
    create_glossary_category_assets,
    create_glossary_assets,
    create_glossary_term_assets,
    get_workflow_package_names,
    get_workflows,
    get_workflow_runs,
    create_data_domain_assets,
    create_data_product_assets,
    create_dq_rules,
    schedule_dq_rules,
    delete_dq_rules,
    update_dq_rules,
    UpdatableAttribute,
    CertificateStatus,
    UpdatableAsset,
    TermOperations,
)
from pyatlan.model.lineage import LineageDirection
from utils.parameters import (
    parse_json_parameter,
    parse_list_parameter,
)
from middleware import ToolRestrictionMiddleware
from settings import get_settings


mcp = FastMCP("Atlan MCP Server")

# Get restricted tools from environment variable or use default
restricted_tools_env = os.getenv("RESTRICTED_TOOLS", "")
if restricted_tools_env:
    restricted_tools = [
        tool.strip() for tool in restricted_tools_env.split(",") if tool.strip()
    ]
else:
    # Default configuration - modify this list to restrict specific tools
    restricted_tools = []

tool_restriction = ToolRestrictionMiddleware(restricted_tools=restricted_tools)
mcp.add_middleware(tool_restriction)


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
        connection_qualified_name (str, optional): Connection qualified name to filter by. ex: default/snowflake/123456/abc
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

        # Search for assets missing descriptions from the database/connection default/snowflake/123456/abc
        missing_desc = search_assets(
            connection_qualified_name="default/snowflake/123456/abc",
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

        # For multiple asset types queries. ex: Search for Table, Column, or View assets from the database/connection default/snowflake/123456/abc
        assets = search_assets(
            connection_qualified_name="default/snowflake/123456/abc",
            conditions={
                "type_name": ["Table", "Column", "View"],
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

        # Find popular but expensive assets (cost optimization)
        search_assets(
            conditions={
                "popularityScore": {"operator": "gte", "value": 0.8},
                "sourceReadQueryCost": {"operator": "gte", "value": 1000}
            },
            include_attributes=["sourceReadExpensiveQueryRecordList", "sourceCostUnit"]
        )

        # Find unused assets accessed before 2024
        search_assets(
            conditions={"sourceLastReadAt": {"operator": "lt", "value": 1704067200000}}, # Unix epoch in milliseconds
            include_attributes=["sourceReadCount", "sourceLastReadAt"]
        )

        # Get top users for a specific table
        # Note: Can't directly filter by user, but can retrieve the list
        search_assets(
            conditions={"name": "customer_transactions"},
            include_attributes=["sourceReadTopUserList", "sourceReadUserCount"]
        )

        # Find frequently accessed uncertified assets (governance gap)
        search_assets(
            conditions={
                "sourceReadUserCount": {"operator": "gte", "value": 10},
                "certificate_status": {"operator": "ne", "value": "VERIFIED"}
            }
        )

        # Query assets in specific connection with cost filters
        search_assets(
            connection_qualified_name="default/snowflake/123456",
            conditions={"sourceTotalCost": {"operator": "gte", "value": 500}},
            sort_by="sourceTotalCost",
            sort_order="DESC",
            include_attributes=[
                "sourceReadQueryComputeCostRecordList",  # Shows breakdown by warehouse
                "sourceQueryComputeCostList",  # List of warehouses used
                "sourceCostUnit"
            ]
        )

    The search supports various analytics attributes following similar patterns:
    - Usage Metrics:
        - `sourceReadCount`, `sourceReadUserCount` - Filter by read frequency or user diversity
        - `sourceLastReadAt`, `lastRowChangedAt` - Time-based filtering (Unix timestamp in ms)
        - `popularityScore` - Float value 0-1 indicating asset popularity

    - Cost Metrics:
        - `sourceReadQueryCost`, `sourceTotalCost` - Filter by cost thresholds
        - Include `sourceCostUnit` in attributes to get cost units
        - Include `sourceReadExpensiveQueryRecordList` for detailed breakdowns

    - User Analytics:
        - `sourceReadTopUserList`, `sourceReadRecentUserList` - Get user lists
        - `sourceReadTopUserRecordList`, `sourceReadRecentUserRecordList` - Get detailed records

    - Query Analytics:
        - `sourceReadPopularQueryRecordList` - Popular queries for the asset
        - `lastRowChangedQuery` - Query that last modified the asset

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
    include_attributes=None,
):
    """
    Traverse asset lineage in specified direction.

    By default, essential attributes are included in results. Additional attributes can be
    specified via include_attributes parameter for richer lineage information.

    Args:
        guid (str): GUID of the starting asset
        direction (str): Direction to traverse ("UPSTREAM" or "DOWNSTREAM")
        depth (int, optional): Maximum depth to traverse. Defaults to 1000000.
        size (int, optional): Maximum number of results to return. Defaults to 10.
        immediate_neighbors (bool, optional): Only return immediate neighbors. Defaults to True.
        include_attributes (List[str], optional): List of additional attribute names to include in results.
            These will be added to the default set.

    Default Attributes (always included):
        - name, display_name, description, qualified_name, user_description
        - certificate_status, owner_users, owner_groups
        - connector_name, has_lineage, source_created_at, source_updated_at
        - readme, asset_tags

    Returns:
        Dict[str, Any]: Dictionary containing:
            - assets: List of assets in the lineage with processed attributes
            - error: None if no error occurred, otherwise the error message

    Examples:
        # Get lineage with default attributes
        lineage = traverse_lineage_tool(
            guid="asset-guid-here",
            direction="DOWNSTREAM",
            depth=1000,
            size=10
        )
    """
    try:
        direction_enum = LineageDirection[direction.upper()]
    except KeyError:
        raise ValueError(
            f"Invalid direction: {direction}. Must be either 'UPSTREAM' or 'DOWNSTREAM'"
        )

    # Parse include_attributes parameter if provided
    parsed_include_attributes = parse_list_parameter(include_attributes)

    return traverse_lineage(
        guid=guid,
        direction=direction_enum,
        depth=int(depth),
        size=int(size),
        immediate_neighbors=bool(immediate_neighbors),
        include_attributes=parsed_include_attributes,
    )


@mcp.tool()
def update_assets_tool(
    assets,
    attribute_name,
    attribute_values,
):
    """
    Update one or multiple assets with different values for attributes or term operations.

    Args:
        assets (Union[Dict[str, Any], List[Dict[str, Any]]]): Asset(s) to update.
            Can be a single UpdatableAsset or a list of UpdatableAsset objects.
            For asset of type_name=AtlasGlossaryTerm or type_name=AtlasGlossaryCategory, each asset dictionary MUST include a "glossary_guid" key which is the GUID of the glossary that the term belongs to.
        attribute_name (str): Name of the attribute to update.
            Supports "user_description", "certificate_status", "readme", and "term".
        attribute_values (List[Union[str, Dict[str, Any]]]): List of values to set for the attribute.
            For certificateStatus, only "VERIFIED", "DRAFT", or "DEPRECATED" are allowed.
            For readme, the value must be a valid Markdown string.
            For term, the value must be a dict with "operation" and "term_guids" keys.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - updated_count: Number of assets successfully updated
            - errors: List of any errors encountered
            - operation: The operation that was performed (for term operations)

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

        # Append terms to a single asset
        result = update_assets_tool(
            assets={
                "guid": "asset-guid-here",
                "name": "Customer Name Column",
                "type_name": "Column",
                "qualified_name": "default/snowflake/123456/abc/CUSTOMER_NAME"
            },
            attribute_name="term",
            attribute_values=[{
                "operation": "append",
                "term_guids": ["term-guid-1", "term-guid-2"]
            }]
        )

        # Replace all terms on multiple assets
        result = update_assets_tool(
            assets=[
                {
                    "guid": "asset-guid-1",
                    "name": "Table 1",
                    "type_name": "Table",
                    "qualified_name": "default/snowflake/123456/abc/TABLE_1"
                },
                {
                    "guid": "asset-guid-2",
                    "name": "Table 2",
                    "type_name": "Table",
                    "qualified_name": "default/snowflake/123456/abc/TABLE_2"
                }
            ],
            attribute_name="term",
            attribute_values=[
                {
                    "operation": "replace",
                    "term_guids": ["new-term-for-table-1-guid-1", "new-term-for-table-1-guid-2"]
                },
                {
                    "operation": "replace",
                    "term_guids": ["new-term-for-table-2-guid-1", "new-term-for-table-2-guid-2"]
                }
            ]
        )

        # Remove specific terms from an asset
        result = update_assets_tool(
            assets={
                "guid": "asset-guid-here",
                "name": "Customer Data Table",
                "type_name": "Table",
                "qualified_name": "default/snowflake/123456/abc/CUSTOMER_DATA"
            },
            attribute_name="term",
            attribute_values=[{
                "operation": "remove",
                "term_guids": ["term-guid-to-remove"]
            }]
        )
    """
    try:
        # Parse JSON parameters
        parsed_assets = parse_json_parameter(assets)
        parsed_attribute_values = parse_list_parameter(attribute_values)

        # Convert string attribute name to enum
        attr_enum = UpdatableAttribute(attribute_name)

        # Handle term operations - convert dict to TermOperations object
        if attr_enum == UpdatableAttribute.TERM:
            term_operations = []
            for value in parsed_attribute_values:
                if isinstance(value, dict):
                    term_operations.append(TermOperations(**value))
                else:
                    return {
                        "error": "Term attribute values must be dictionaries with 'operation' and 'term_guids' keys",
                        "updated_count": 0,
                    }
            parsed_attribute_values = term_operations
        # For certificate status, convert values to enum
        elif attr_enum == UpdatableAttribute.CERTIFICATE_STATUS:
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
def query_asset_tool(
    sql: str, connection_qualified_name: str, default_schema: str | None = None
):
    """
    Execute a SQL query on a table/view asset.

    This tool enables querying table/view assets on the source similar to
    what's available in the insights table. It uses the Atlan query capabilities
    to execute SQL against connected data sources.

    CRITICAL: Use READ-ONLY queries to retrieve data. Write and modify queries are not supported by this tool.


    Args:
        sql (str): The SQL query to execute (read-only queries allowed)
        connection_qualified_name (str): Connection qualified name to use for the query.
            This is the same parameter used in search_assets_tool.
            You can find this value by searching for Table/View assets using search_assets_tool
            and extracting the first part of the 'qualifiedName' attribute.
            Example: from "default/snowflake/1657275059/LANDING/FRONTEND_PROD/PAGES"
            use "default/snowflake/1657275059"
        default_schema (str, optional): Default schema name to use for unqualified
            objects in the SQL, in the form "DB.SCHEMA"
            (e.g., "RAW.WIDEWORLDIMPORTERS_WAREHOUSE")

    Examples:
        # Use case: How to query the PAGES table and retrieve the first 10 rows
        # Find tables to query using search_assets_tool
        tables = search_assets_tool(
            asset_type="Table",
            conditions={"name": "PAGES"},
            limit=5
        )
        # Extract connection info from the table's qualifiedName
        # Example qualifiedName: "default/snowflake/1657275059/LANDING/FRONTEND_PROD/PAGES"
        # connection_qualified_name: "default/snowflake/1657275059"
        # database.schema: "LANDING.FRONTEND_PROD"

        # Query the table using extracted connection info
        result = query_asset_tool(
            sql='SELECT * FROM PAGES LIMIT 10',
            connection_qualified_name="default/snowflake/1657275059",
            default_schema="LANDING.FRONTEND_PROD"
        )

        # Query without specifying default schema (fully qualified table names)
        result = query_asset_tool(
            sql='SELECT COUNT(*) FROM "LANDING"."FRONTEND_PROD"."PAGES"',
            connection_qualified_name="default/snowflake/1657275059"
        )

        # Complex analytical query on PAGES table
        result = query_asset_tool(
            sql='''
            SELECT
                page_type,
                COUNT(*) AS page_count,
                AVG(load_time) AS avg_load_time,
                MAX(views) AS max_views
            FROM PAGES
            WHERE created_date >= '2024-01-01'
            GROUP BY page_type
            ORDER BY page_count DESC
            ''',
            connection_qualified_name="default/snowflake/1657275059",
            default_schema="LANDING.FRONTEND_PROD"
        )
    """
    return query_asset(sql, connection_qualified_name, default_schema)


@mcp.tool()
def create_glossaries(glossaries) -> List[Dict[str, Any]]:
    """
    Create one or multiple AtlasGlossary assets in Atlan.

    IMPORTANT BUSINESS RULES & CONSTRAINTS:
    - Check for duplicate names within the same request and ask user to choose different names
    - Do NOT use search tool before creating glossaries - Atlan will handle existence validation
    - If user gives ambiguous instructions, ask clarifying questions

    Args:
        glossaries (Union[Dict[str, Any], List[Dict[str, Any]]]): Either a single glossary
            specification (dict) or a list of glossary specifications. Each specification
            can be a dictionary containing:
            - name (str): Name of the glossary (required)
            - user_description (str, optional): Detailed description of the glossary
              proposed by the user
            - certificate_status (str, optional): Certification status
              ("VERIFIED", "DRAFT", or "DEPRECATED")

    Returns:
        List[Dict[str, Any]]: List of dictionaries, each with details for a created glossary:
            - guid: The GUID of the created glossary
            - name: The name of the glossary
            - qualified_name: The qualified name of the created glossary


    Examples:
        Multiple glossaries creation:
        [
            {
                "name": "Business Terms",
                "user_description": "Common business terminology",
                "certificate_status": "VERIFIED"
            },
            {
                "name": "Technical Dictionary",
                "user_description": "Technical terminology and definitions",
                "certificate_status": "DRAFT"
            }
        ]
    """

    # Parse parameters to handle JSON strings using shared utility
    try:
        glossaries = parse_json_parameter(glossaries)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON format for glossaries parameter: {str(e)}"}

    return create_glossary_assets(glossaries)


@mcp.tool()
def create_glossary_terms(terms) -> List[Dict[str, Any]]:
    """
    Create one or multiple AtlasGlossaryTerm assets in Atlan.

    IMPORTANT BUSINESS RULES & CONSTRAINTS:
    - Within a glossary, a term (single GUID) can be associated with many categories
    - Two terms with the same name CANNOT exist within the same glossary (regardless of categories)
    - A term is always anchored to a glossary and may also be associated with one or more categories inside the same glossary
    - Before creating a term, perform a single search to check if the glossary, categories, or term with the same name already exist. Search for all relevant glossaries, categories, and terms in one call. Skip this step if you already have the required GUIDs.
    - Example call for searching glossary categories and terms before term creation(Query - create a term fighterz under category Characters and Locations under Marvel Cinematic Universe (MCU) glossary):
        {
            "limit": 10,
            "conditions": {
                "type_name": ["AtlasGlossary", "AtlasGlossaryCategory","AtlasGlossaryTerm"],
                "name": ["Marvel Cinematic Universe (MCU)", "Characters", "Locations","fighterz"]
            }
        }

    Args:
        terms (Union[Dict[str, Any], List[Dict[str, Any]]]): Either a single term
            specification (dict) or a list of term specifications. Each specification
            can be a dictionary containing:
            - name (str): Name of the term (required)
            - glossary_guid (str): GUID of the glossary this term belongs to (required)
            - user_description (str, optional): Detailed description of the term
              proposed by the user
            - certificate_status (str, optional): Certification status
              ("VERIFIED", "DRAFT", or "DEPRECATED")
            - category_guids (List[str], optional): List of category GUIDs this term
              belongs to.

    Returns:
        List[Dict[str, Any]]: List of dictionaries, each with details for a created term:
            - guid: The GUID of the created term
            - name: The name of the term
            - qualified_name: The qualified name of the created term

    Examples:
        Multiple terms creation:
        [
            {
                "name": "Customer",
                "glossary_guid": "glossary-guid-here",
                "user_description": "An individual or organization that purchases goods or services",
                "certificate_status": "VERIFIED"
            },
            {
                "name": "Annual Recurring Revenue",
                "glossary_guid": "glossary-guid-here",
                "user_description": "The yearly value of recurring revenue from customers",
                "certificate_status": "DRAFT",
                "category_guids": ["category-guid-1"]
            }
        ]
    """
    # Parse parameters to handle JSON strings using shared utility
    try:
        terms = parse_json_parameter(terms)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON format for terms parameter: {str(e)}"}

    return create_glossary_term_assets(terms)


@mcp.tool()
def create_glossary_categories(categories) -> List[Dict[str, Any]]:
    """
    Create one or multiple AtlasGlossaryCategory assets in Atlan.

    IMPORTANT BUSINESS RULES & CONSTRAINTS:
    - There cannot be two categories with the same name under the same glossary (at the same level)
    - Under a parent category, there cannot be subcategories with the same name (at the same level)
    - Categories with the same name can exist under different glossaries (this is allowed)
    - Cross-level naming is allowed: category "a" can have subcategory "b", and category "b" can have subcategory "a"
    - Example allowed structure: Glossary "bui" → category "a" → subcategory "b" AND category "b" → subcategory "a"
    - Always check for duplicate names at the same level and ask user to choose different names
    - Before creating a category, perform a single search to check if the glossary or categories with the same name already exist. Skip this step if you already have the required GUIDs.
    - Example call for searching glossary and categories before category creation(Query - create categories Locations and Characters under Marvel Cinematic Universe (MCU) glossary):
        {
            "limit": 10,
            "conditions": {
                "type_name": ["AtlasGlossary", "AtlasGlossaryCategory"],
                "name": ["Marvel Cinematic Universe (MCU)", "Characters", "Locations"]
            }
        }
    - If user gives ambiguous instructions, ask clarifying questions

    Args:
        categories (Union[Dict[str, Any], List[Dict[str, Any]]]): Either a single category
            specification (dict) or a list of category specifications. Each specification
            can be a dictionary containing:
            - name (str): Name of the category (required)
            - glossary_guid (str): GUID of the glossary this category belongs to (required)
            - user_description (str, optional): Detailed description of the category
              proposed by the user
            - certificate_status (str, optional): Certification status
              ("VERIFIED", "DRAFT", or "DEPRECATED")
            - parent_category_guid (str, optional): GUID of the parent category if this
              is a subcategory

    Returns:
        List[Dict[str, Any]]: List of dictionaries, each with details for a created category:
            - guid: The GUID of the created category
            - name: The name of the category
            - qualified_name: The qualified name of the created category

    Examples:
        Multiple categories creation:
        [
            {
                "name": "Customer Data",
                "glossary_guid": "glossary-guid-here",
                "user_description": "Terms related to customer information and attributes",
                "certificate_status": "VERIFIED"
            },
            {
                "name": "PII",
                "glossary_guid": "glossary-guid-here",
                "parent_category_guid": "parent-category-guid-here",
                "user_description": "Subcategory for PII terms",
                "certificate_status": "DRAFT"
            }
        ]
    """
    # Parse parameters to handle JSON strings using shared utility
    try:
        categories = parse_json_parameter(categories)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON format for categories parameter: {str(e)}"}

    return create_glossary_category_assets(categories)


@mcp.tool()
def get_workflow_package_names_tool() -> List[str]:
    """
    Get the values of all available workflow packages.

    This tool returns a list of all workflow package names that can be used
    with other workflow tools.

    Returns:
        List[str]: List of workflow package names (e.g., ['atlan-snowflake', 'atlan-bigquery', ...])

    Examples:
        # Get all workflow package names
        packages = get_workflow_package_names_tool()
    """
    return get_workflow_package_names()


@mcp.tool()
def get_workflows_tool(
    id: str | None = None,
    workflow_package_name: str | None = None,
    max_results: int = 10,
) -> Dict[str, Any]:
    """
    Retrieve workflows by ID or by package type.

    This tool supports two main use cases:
    1. Get a specific workflow by ID (returns full workflow details including steps and spec)
    2. Get multiple workflows by package type (returns metadata only, no full details)

    IMPORTANT: When getting by ID, this tool returns full workflow instructions with all steps and transformations.
    When getting by type, this tool returns only basic metadata to avoid large responses.

    Note: This tool only returns workflows (templates), not workflow_runs.
    To get workflow_run information, use get_workflow_runs_tool.

    When to use this tool:
    - Use when you need to get a specific workflow by ID with full details (steps, spec, transformations)
    - Use when you need to list multiple workflows by package type (metadata only)
    - Use when you need to understand the full workflow execution flow (by ID only)
    - Do NOT use if you need workflow_run (execution) information

    Args:
        id (str, optional): The unique identifier (ID) of the workflow (e.g., 'atlan-snowflake-miner-1714638976').
            If provided, returns a single workflow with full details (workflow_steps and workflow_spec).
            Either id or workflow_package_name must be provided, but not both.
        workflow_package_name (str, optional): The workflow package name (e.g., 'atlan-snowflake', 'atlan-bigquery', 'SNOWFLAKE').
            Can be the full package name like 'atlan-snowflake' or the enum name like 'SNOWFLAKE'.
            If provided, returns list of workflows with metadata only (no workflow_steps or workflow_spec).
            Either id or workflow_package_name must be provided, but not both.
        max_results (int, optional): Maximum number of workflows to return when getting by type. Defaults to 10.
            Only used when workflow_package_name is provided.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - workflows: List of workflow dictionaries. When getting by ID, contains single item.
                Each workflow contains:
                    - template_name: Name of the template
                    - package_name, package_version: Package information
                    - source_system, source_category, workflow_type: Source information
                    - certified, verified: Certification status
                    - creator_email, creator_username: Creator information
                    - modifier_email, modifier_username: Last modifier information
                    - creation_timestamp: When template was created
                    - package_author, package_description, package_repository: Package metadata
                    - workflow_steps: Workflow steps (only when getting by ID)
                    - workflow_spec: Full workflow specification (only when getting by ID)
            - total: Total count of workflows (1 when getting by ID, actual count when getting by type)
            - error: None if no error occurred, otherwise the error message

    Examples:
        # Get a specific workflow by ID (full details with steps and spec)
        result = get_workflows_tool(id="atlan-snowflake-miner-1714638976")
        workflow = result.get("workflows", [])[0]  # Single workflow in list
        # workflow contains complete workflow definition with workflow_steps and workflow_spec

        # Get Snowflake workflows by type (metadata only)
        result = get_workflows_tool(workflow_package_name="atlan-snowflake")
        workflows = result.get("workflows", [])  # List of workflows

        # Get BigQuery workflows with custom limit
        result = get_workflows_tool(workflow_package_name="atlan-bigquery", max_results=50)

        # Get workflows using enum name
        result = get_workflows_tool(workflow_package_name="SNOWFLAKE")
    """
    return get_workflows(
        id=id,
        workflow_package_name=workflow_package_name,
        max_results=max_results,
    )


@mcp.tool()
def get_workflow_runs_tool(
    workflow_name: str | None = None,
    workflow_phase: str | None = None,
    status: str
    | None = None,  # This is technically a list but we get the input as a string so we parse it into a list
    started_at: str | None = None,
    finished_at: str | None = None,
    from_: int = 0,
    size: int = 100,
) -> Dict[str, Any]:
    """
    Retrieve workflow_runs with flexible filtering options.

    This tool supports two main use cases:
    1. Filter by specific workflow name and phase (single workflow)
    2. Filter across all workflows by status list and optional time ranges

    Each workflow_run contains execution details, timing, resource usage, and status information.

    IMPORTANT: This tool returns only metadata and execution status. It does NOT return full workflow
    instructions, steps, or transformations. To get complete workflow details including all steps and
    transformations, use get_workflows_tool with an id parameter instead.

    When to use this tool:
    - Use when you need to find all workflow_runs of a specific workflow by execution phase
        → Provide workflow_name AND workflow_phase (do NOT use status)
    - Use when you need to find workflow_runs across multiple workflows filtered by status and time
        → Provide status (and optionally started_at/finished_at), do NOT provide workflow_name or workflow_phase
    - Use when monitoring workflow execution patterns or analyzing failures
    - Use when you need execution metadata (status, timing, resource usage) for multiple workflow_runs
    - Do NOT use if you need the complete workflow specification (use get_workflows_tool with id instead)

    Args:
        workflow_name (str, optional): Name of the workflow (template) as displayed in the UI
            (e.g., 'atlan-snowflake-miner-1714638976'). If provided, filters runs for that specific workflow.
            This refers to the workflow name, not individual workflow_run IDs.
        workflow_phase (str, optional): Phase of the workflow_run. Common values: 'Succeeded', 'Running', 'Failed', 'Error', 'Pending'.
            Case-insensitive matching is supported.
            REQUIRED when workflow_name is provided. DO NOT use status when workflow_name is provided.
        status (List[str], optional): Array/list of workflow_run phases to filter by.
            IMPORTANT: Must be an array/list type, NOT a JSON string.
            Correct format: ["Succeeded", "Failed"] (array/list)
            Incorrect format: '["Succeeded", "Failed"]' (string - will be rejected by schema validation)
            Common values:
                - 'Succeeded': Successfully completed workflow_runs
                - 'Failed': Workflow_runs that failed
                - 'Running': Currently executing workflow_runs
                - 'Error': Workflow_runs that encountered errors
                - 'Pending': Workflow_runs waiting to start
            Case-insensitive matching is supported.
            REQUIRED when workflow_name is NOT provided. DO NOT use status when workflow_name is provided - use workflow_phase instead.
            Example: ["Succeeded", "Failed"]  # Array/list, not a string

    Parameter Usage Rules:
        - If workflow_name is provided: MUST use workflow_phase (single phase string). Do NOT use status.
        - If workflow_name is NOT provided: MUST use status (list of phases). Do NOT use workflow_phase.
        - These are mutually exclusive usage patterns - do not mix them.
        started_at (str, optional): Lower bound on 'status.startedAt' timestamp. Accepts:
            - Relative time format: 'now-2h', 'now-24h', 'now-7d', 'now-30d'
            - ISO 8601 format: '2024-01-01T00:00:00Z'
            Filters workflow_runs that started at or after this time.
            Only used when workflow_name is not provided.
        finished_at (str, optional): Lower bound on 'status.finishedAt' timestamp. Accepts:
            - Relative time format: 'now-1h', 'now-12h'
            - ISO 8601 format: '2024-01-01T00:00:00Z'
            Filters workflow_runs that finished at or after this time.
            Only used when workflow_name is not provided.
        from_ (int, optional): Starting index of the search results for pagination. Defaults to 0.
        size (int, optional): Maximum number of search results to return. Defaults to 100.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - runs: List of workflow_run dictionaries. Each workflow_run contains:
                Run Metadata:
                - run_id: Unique identifier for this workflow_run
                - run_phase: Execution phase (Succeeded, Running, Failed, etc.)
                - run_started_at: When the workflow_run started (ISO timestamp)
                - run_finished_at: When the workflow_run finished (ISO timestamp, None if still running)
                - run_estimated_duration: Estimated execution duration
                - run_progress: Progress indicator (e.g., "1/3")
                - run_cpu_usage: CPU resource usage duration
                - run_memory_usage: Memory resource usage duration

                Workflow Metadata:
                - workflow_id: Reference to the workflow (template) used
                - workflow_package_name: Package identifier
                - workflow_cron_schedule: Cron schedule if scheduled
                - workflow_cron_timezone: Timezone for cron schedule
                - workflow_creator_id, workflow_creator_email, workflow_creator_username: Creator information
                - workflow_modifier_id, workflow_modifier_email, workflow_modifier_username: Last modifier information
                - workflow_creation_timestamp: When the workflow was created
                - workflow_archiving_status: Archiving status
            - total: Total count of workflow_runs matching the criteria (may be larger than the returned list if paginated)
            - error: None if no error occurred, otherwise the error message

    Examples:
        # CORRECT: Get succeeded workflow_runs for a specific workflow (use workflow_phase, NOT status)
        result = get_workflow_runs_tool(workflow_name="atlan-snowflake-miner-1714638976", workflow_phase="Succeeded")

        # CORRECT: Get running workflow_runs for a specific workflow (use workflow_phase, NOT status)
        result = get_workflow_runs_tool(workflow_name="atlan-snowflake-miner-1714638976", workflow_phase="Running")

        # CORRECT: Get failed workflow_runs with pagination (use workflow_phase, NOT status)
        result = get_workflow_runs_tool(workflow_name="atlan-snowflake-miner-1714638976", workflow_phase="Failed", from_=0, size=50)

        # CORRECT: Get succeeded workflow_runs from the last 2 hours (across all workflows - use status, NOT workflow_phase)
        result = get_workflow_runs_tool(status=["Succeeded"], started_at="now-2h")

        # CORRECT: Get failed workflow_runs from the last 24 hours (across all workflows - use status, NOT workflow_phase)
        result = get_workflow_runs_tool(status=["Failed"], started_at="now-24h")

        # CORRECT: Get multiple statuses with both time filters (across all workflows - use status, NOT workflow_phase)
        result = get_workflow_runs_tool(
            status=["Succeeded", "Failed"],
            started_at="now-7d",
            finished_at="now-1h"
        )

        # CORRECT: Get running workflow_runs (across all workflows - use status, NOT workflow_phase)
        result = get_workflow_runs_tool(status=["Running"])

        # Analyze workflow_run durations
        runs = result.get("runs", [])
        for run in runs:
            if run.get("run_finished_at") and run.get("run_started_at"):
                print(f"Workflow run {run['run_id']} took {run.get('run_estimated_duration')}")

        # Analyze failure rates
        failed_runs = [r for r in result.get("runs", []) if r.get("run_phase") == "Failed"]
        print(f"Found {len(failed_runs)} failed workflow_runs in the time range")
    """
    try:
        # Parse list parameter if it comes as a JSON string (common with MCP clients)
        status = parse_list_parameter(status)
    except (json.JSONDecodeError, ValueError) as e:
        return {
            "runs": [],
            "total": 0,
            "error": f"Parameter parsing error for status: {str(e)}",
        }

    return get_workflow_runs(
        workflow_name=workflow_name,
        workflow_phase=workflow_phase,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        from_=from_,
        size=size,
    )


@mcp.tool()
def create_domains(domains) -> List[Dict[str, Any]]:
    """
    Create Data Domains or Sub Domains in Atlan.

    IMPORTANT BUSINESS RULES & CONSTRAINTS:
    - Before creating a domain/subdomain, you may want to search for existing
      domains to avoid duplicates or to get the qualified_name for parent relationships
    - Domain names must be unique at the top level
    - Subdomain names must be unique within the same parent domain

    Args:
        domains (Union[Dict[str, Any], List[Dict[str, Any]]]): Either a single domain
            specification (dict) or a list of domain specifications.

    For Data Domain:
        - name (str): Name of the domain (required)
        - user_description (str, optional): Detailed description
        - certificate_status (str, optional): "VERIFIED", "DRAFT", or "DEPRECATED"

    For Sub Domain:
        - name (str): Name of the subdomain (required)
        - parent_domain_qualified_name (str): Qualified name of parent domain (required)
        - user_description (str, optional): Detailed description
        - certificate_status (str, optional): "VERIFIED", "DRAFT", or "DEPRECATED"

    Returns:
        List[Dict[str, Any]]: List of dictionaries, each with details for a created asset:
            - guid: The GUID of the created asset
            - name: The name of the asset
            - qualified_name: The qualified name of the created asset

    Examples:
        # Create a single Data Domain
        create_domains({
            "name": "Marketing",
            "user_description": "Marketing data domain",
            "certificate_status": "VERIFIED"
        })

        # Create a Sub Domain under an existing domain
        create_domains({
            "name": "Social Marketing",
            "parent_domain_qualified_name": "default/domain/marketing",
            "user_description": "Social media marketing subdomain",
            "certificate_status": "DRAFT"
        })

        # Create multiple domains in one call
        create_domains([
            {
                "name": "Sales",
                "user_description": "Sales data domain"
            },
            {
                "name": "E-commerce Sales",
                "parent_domain_qualified_name": "default/domain/sales",
                "user_description": "E-commerce sales subdomain"
            }
        ])
    """
    # Parse parameters to handle JSON strings using shared utility
    try:
        domains = parse_json_parameter(domains)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON format for domains parameter: {str(e)}"}

    return create_data_domain_assets(domains)


@mcp.tool()
def create_data_products(products) -> List[Dict[str, Any]]:
    """
    Create Data Products in Atlan.

    IMPORTANT BUSINESS RULES & CONSTRAINTS:
    - Before creating a product, you may want to search for existing domains
      to get the qualified_name for the domain relationship
    - Product names must be unique within the same domain
    - At least one asset GUID must be provided for each product

    Args:
        products (Union[Dict[str, Any], List[Dict[str, Any]]]): Either a single product
            specification (dict) or a list of product specifications.

    For Data Product:
        - name (str): Name of the product (required)
        - domain_qualified_name (str): Qualified name of the domain (required)
        - asset_guids (List[str]): List of asset GUIDs to link to this product (required).
          At least one asset GUID must be provided. Use search_assets_tool to find asset GUIDs.
        - user_description (str, optional): Detailed description
        - certificate_status (str, optional): "VERIFIED", "DRAFT", or "DEPRECATED"

    Returns:
        List[Dict[str, Any]]: List of dictionaries, each with details for a created asset:
            - guid: The GUID of the created asset
            - name: The name of the asset
            - qualified_name: The qualified name of the created asset

    Examples:
        # Create a Data Product with linked assets (asset_guids required)
        # First, search for assets to get their GUIDs using search_assets_tool
        create_data_products({
            "name": "Marketing Influence",
            "domain_qualified_name": "default/domain/marketing",
            "user_description": "Product for marketing influence analysis",
            "asset_guids": ["asset-guid-1", "asset-guid-2"]  # GUIDs from search_assets_tool
        })

        # Create multiple products in one call
        create_data_products([
            {
                "name": "Sales Analytics",
                "domain_qualified_name": "default/domain/sales",
                "user_description": "Sales analytics product",
                "asset_guids": ["table-guid-1", "table-guid-2"]
            },
            {
                "name": "Customer Insights",
                "domain_qualified_name": "default/domain/marketing",
                "user_description": "Customer insights product",
                "asset_guids": ["view-guid-1"]
            }
        ])
    """
    # Parse parameters to handle JSON strings using shared utility
    try:
        products = parse_json_parameter(products)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON format for products parameter: {str(e)}"}

    return create_data_product_assets(products)


@mcp.tool()
def create_dq_rules_tool(rules):
    """
    Create one or multiple data quality rules in Atlan.

    Supports all rule types: column-level, table-level, and custom SQL rules.
    Rules can be created individually or in bulk for efficient setup.

    Args:
        rules (Union[Dict[str, Any], List[Dict[str, Any]]]): Either a single rule
            specification or a list of rule specifications. Each specification
            must include:
            - rule_type (str): Type of rule (see Supported Rule Types) [REQUIRED]
            - asset_qualified_name (str): Qualified name of the asset (Table, View, MaterialisedView, or SnowflakeDynamicTable) [REQUIRED]
            - asset_type (str): Type of asset - "Table" | "View" | "MaterialisedView" | "SnowflakeDynamicTable" [OPTIONAL, default: "Table"]
            - threshold_value (int/float): Threshold value for comparison [REQUIRED]
            - column_qualified_name (str): Column qualified name [REQUIRED for column-level rules, NOT for Row Count/Custom SQL]
            - threshold_compare_operator (str): Comparison operator (EQUAL, GREATER_THAN, etc.) [OPTIONAL, default varies by rule]
            - threshold_unit (str): Time unit for Freshness rules (DAYS, HOURS, MINUTES) [REQUIRED for Freshness, N/A for others]
            - alert_priority (str): Alert priority level (LOW, NORMAL, URGENT) [OPTIONAL, default: NORMAL]
            - row_scope_filtering_enabled (bool): Enable row-level filtering [OPTIONAL]
            - rule_conditions (List[Dict]): Conditions for String Length/Regex/Valid Values [REQUIRED for conditional rules]
            - custom_sql (str): SQL query [REQUIRED for Custom SQL rules]
            - rule_name (str): Name for the rule [REQUIRED for Custom SQL rules]
            - dimension (str): DQ dimension [REQUIRED for Custom SQL rules]
            - description (str): Rule description [OPTIONAL]

    Returns:
        Dict[str, Any]: Dictionary containing:
            - created_count: Number of rules successfully created
            - created_rules: List of created rules with guid, qualified_name, rule_type
            - errors: List of any errors encountered

    Examples:
        # Column-level rules (Null Count, Min/Max Value, Unique/Duplicate Count, etc.)
        rule = create_dq_rules_tool({
            "rule_type": "Null Count",  # or "Min Value", "Max Value", "Unique Count", etc.
            "asset_qualified_name": "default/snowflake/123/DB/SCHEMA/TABLE",
            "column_qualified_name": "default/snowflake/123/DB/SCHEMA/TABLE/EMAIL",
            "threshold_compare_operator": "LESS_THAN_EQUAL",  # EQUAL, GREATER_THAN, etc.
            "threshold_value": 5,
            "alert_priority": "URGENT",  # LOW, NORMAL, URGENT
            "row_scope_filtering_enabled": True,
            "description": "Email column should have minimal nulls"
        })

        # Conditional rules (String Length, Regex, Valid Values)
        rule = create_dq_rules_tool({
            "rule_type": "String Length",  # or "Regex", "Valid Values"
            "asset_qualified_name": "default/snowflake/123/DB/SCHEMA/TABLE",
            "column_qualified_name": "default/snowflake/123/DB/SCHEMA/TABLE/PHONE",
            "threshold_value": 10,
            "alert_priority": "URGENT",
            "rule_conditions": [{
                "type": "STRING_LENGTH_BETWEEN",  # See Rule Condition Types below
                "min_value": 10,
                "max_value": 15
            }],
            # For Regex: {"type": "REGEX_NOT_MATCH", "value": "pattern"}
            # For Valid Values: {"type": "IN_LIST", "value": ["ACTIVE", "INACTIVE"]}
            "row_scope_filtering_enabled": True
        })

        # Table-level (Row Count) and Time-based (Freshness)
        rule = create_dq_rules_tool({
            "rule_type": "Row Count",  # No column_qualified_name needed
            "asset_qualified_name": "default/snowflake/123/DB/SCHEMA/TABLE",
            "asset_type": "Table",  # Optional: "Table" (default), "View", "MaterialisedView", "SnowflakeDynamicTable"
            "threshold_compare_operator": "GREATER_THAN_EQUAL",
            "threshold_value": 1000,
            "alert_priority": "URGENT"
        })
        # For Freshness: Add "column_qualified_name" + "threshold_unit": "DAYS"/"HOURS"/"MINUTES"

        # Custom SQL rule
        rule = create_dq_rules_tool({
            "rule_type": "Custom SQL",
            "asset_qualified_name": "default/snowflake/123/DB/SCHEMA/TABLE",
            "rule_name": "Revenue Consistency Check",
            "custom_sql": "SELECT COUNT(*) FROM TABLE WHERE revenue < 0 OR revenue > 1000000",
            "threshold_compare_operator": "EQUAL",
            "threshold_value": 0,
            "alert_priority": "URGENT",
            "dimension": "CONSISTENCY",  # See Data Quality Dimensions below
            "description": "Ensure revenue values are within expected range"
        })

        # Bulk creation - Pass array instead of single dict
        rules = create_dq_rules_tool([
            {"rule_type": "Null Count", "column_qualified_name": "...EMAIL", ...},
            {"rule_type": "Duplicate Count", "column_qualified_name": "...USER_ID", ...},
            {"rule_type": "Row Count", "asset_qualified_name": "...", ...}
        ])

    Supported Rule Types:
        Completeness: "Null Count", "Null Percentage", "Blank Count", "Blank Percentage"
        Statistical: "Min Value", "Max Value", "Average", "Standard Deviation"
        Uniqueness: "Unique Count", "Duplicate Count"
        Validity: "Regex", "String Length", "Valid Values"
        Timeliness: "Freshness"
        Volume: "Row Count"
        Custom: "Custom SQL"

    Supported Asset Types:
        "Table", "View", "MaterialisedView", "SnowflakeDynamicTable"

    Valid Alert Priority Levels:
        "LOW", "NORMAL" (default), "URGENT"

    Threshold Operators:
        "EQUAL", "GREATER_THAN", "GREATER_THAN_EQUAL", "LESS_THAN", "LESS_THAN_EQUAL", "BETWEEN"

    Threshold Units (Freshness only):
        "DAYS", "HOURS", "MINUTES"

    Data Quality Dimensions (Custom SQL only):
        "COMPLETENESS", "VALIDITY", "UNIQUENESS", "TIMELINESS", "VOLUME", "ACCURACY", "CONSISTENCY"

    Rule Condition Types:
        String Length: "STRING_LENGTH_EQUALS", "STRING_LENGTH_BETWEEN",
                      "STRING_LENGTH_GREATER_THAN", "STRING_LENGTH_LESS_THAN"
        Regex: "REGEX_MATCH", "REGEX_NOT_MATCH"
        Valid Values: "IN_LIST", "NOT_IN_LIST"
    """
    try:
        parsed_rules = parse_json_parameter(rules)
        return create_dq_rules(parsed_rules)
    except (json.JSONDecodeError, ValueError) as e:
        return {
            "created_count": 0,
            "created_rules": [],
            "errors": [f"Parameter parsing error: {str(e)}"],
        }


@mcp.tool()
def schedule_dq_rules_tool(schedules):
    """
    Schedule data quality rule execution for one or multiple assets.

    Args:
        schedules: Single schedule or list of schedules. Each schedule requires:
            - asset_type (str): "Table", "View", "MaterialisedView", or "SnowflakeDynamicTable"
            - asset_name (str): Name of the asset
            - asset_qualified_name (str): Qualified name of the asset
            - schedule_crontab (str): Cron expression (5 fields: min hour day month weekday)
            - schedule_time_zone (str): Timezone (e.g., "UTC", "America/New_York")

    Returns:
        Dict with scheduled_count, scheduled_assets, and errors.

    Example:
        schedule_dq_rules_tool({
            "asset_type": "Table",
            "asset_name": "CUSTOMERS",
            "asset_qualified_name": "default/snowflake/123/DB/SCHEMA/CUSTOMERS",
            "schedule_crontab": "0 2 * * *",
            "schedule_time_zone": "UTC"
        })
    """
    try:
        parsed_schedules = parse_json_parameter(schedules)
        return schedule_dq_rules(parsed_schedules)
    except (json.JSONDecodeError, ValueError) as e:
        return {
            "scheduled_count": 0,
            "scheduled_assets": [],
            "errors": [f"Parameter parsing error: {str(e)}"],
        }


@mcp.tool()
def delete_dq_rules_tool(rule_guids):
    """
    Delete one or multiple data quality rules in Atlan.

    Args:
        rule_guids: Single rule GUID (string) or list of rule GUIDs to delete.

    Returns:
        Dict with deleted_count, deleted_rules (list of GUIDs), and errors.

    Example:
        # Delete single rule
        delete_dq_rules_tool("rule-guid-123")

        # Delete multiple rules
        delete_dq_rules_tool(["rule-guid-1", "rule-guid-2"])
    """
    try:
        parsed_guids = parse_json_parameter(rule_guids)
        return delete_dq_rules(parsed_guids)
    except (json.JSONDecodeError, ValueError) as e:
        return {
            "deleted_count": 0,
            "deleted_rules": [],
            "errors": [f"Parameter parsing error: {str(e)}"],
        }


@mcp.tool()
def update_dq_rules_tool(rules):
    """
    Update existing data quality rules in Atlan.

    Args:
        rules: Single rule dict or list of rule dicts. Required fields:
            - qualified_name: Rule's qualified name
            - rule_type: Rule type (e.g., "Null Count", "Row Count", "Custom SQL")
            - asset_qualified_name: Table/view qualified name
        Optional fields: threshold_value, threshold_compare_operator, threshold_unit,
        alert_priority, custom_sql, rule_name, dimension, rule_conditions,
        row_scope_filtering_enabled, description

    Returns:
        Dict with updated_count, updated_rules, and errors.

    Examples:
        # Single rule update
        update_dq_rules_tool({
            "qualified_name": "default/snowflake/123/DB/SCHEMA/TABLE/rule/abc-123",
            "rule_type": "Null Count",
            "asset_qualified_name": "default/snowflake/123/DB/SCHEMA/TABLE",
            "threshold_value": 10,
            "alert_priority": "URGENT"
        })

        # Bulk update with conditions
        update_dq_rules_tool([
            {"qualified_name": "...", "rule_type": "Null Count", "threshold_value": 5},
            {"qualified_name": "...", "rule_type": "String Length",
             "rule_conditions": [{"type": "STRING_LENGTH_BETWEEN", "min_value": 10, "max_value": 100}]}
        ])

    Rule Types: "Null Count", "Null Percentage", "Blank Count", "Blank Percentage",
    "Min Value", "Max Value", "Average", "Standard Deviation", "Unique Count",
    "Duplicate Count", "Regex", "String Length", "Valid Values", "Freshness",
    "Row Count", "Custom SQL"

    Alert Priority: "LOW", "NORMAL", "URGENT"
    Operators: "EQUAL", "GREATER_THAN", "GREATER_THAN_EQUAL", "LESS_THAN",
               "LESS_THAN_EQUAL", "BETWEEN"
    Threshold Units: "DAYS", "HOURS", "MINUTES" (Freshness only)
    Dimensions: "COMPLETENESS", "VALIDITY", "UNIQUENESS", "TIMELINESS", "VOLUME",
                "ACCURACY", "CONSISTENCY" (Custom SQL only)
    Condition Types: "STRING_LENGTH_EQUALS", "STRING_LENGTH_BETWEEN",
                     "STRING_LENGTH_GREATER_THAN", "STRING_LENGTH_LESS_THAN",
                     "REGEX_MATCH", "REGEX_NOT_MATCH", "IN_LIST", "NOT_IN_LIST"
    """
    try:
        parsed_rules = parse_json_parameter(rules)
        return update_dq_rules(parsed_rules)
    except (json.JSONDecodeError, ValueError) as e:
        return {
            "updated_count": 0,
            "updated_rules": [],
            "errors": [f"Parameter parsing error: {str(e)}"],
        }


def main():
    """Main entry point for the Atlan MCP Server."""

    settings = get_settings()

    parser = argparse.ArgumentParser(description="Atlan MCP Server")
    parser.add_argument(
        "--transport",
        type=str,
        default=settings.MCP_TRANSPORT,
        choices=["stdio", "sse", "streamable-http"],
        help="Transport protocol (stdio/sse/streamable-http)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=settings.MCP_HOST,
        help="Host to run the server on",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.MCP_PORT,
        help="Port to run the server on",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=settings.MCP_PATH,
        help="Path of the streamable HTTP server",
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


if __name__ == "__main__":
    main()

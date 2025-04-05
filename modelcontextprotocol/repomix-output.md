This file is a merged representation of the entire codebase, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

## Additional Info

# Directory Structure
```
.env.template
.python-version
client.py
pyproject.toml
README.md
server.py
settings.py
tools.py
```

# Files

## File: .env.template
````
ATLAN_BASE_URL=https://domain.atlan.com
ATLAN_API_KEY=your_api_key
````

## File: .python-version
````
3.11
````

## File: client.py
````python
"""Client factory for Atlan."""

import logging

from pyatlan.client.atlan import AtlanClient
from settings import Settings

logger = logging.getLogger(__name__)


def create_atlan_client(settings: Settings) -> AtlanClient:
    """Create an Atlan client instance using the provided settings.

    Args:
        settings: Application settings containing Atlan credentials

    Returns:
        An initialized AtlanClient instance
    """
    try:
        client = AtlanClient(
            base_url=settings.atlan_base_url, api_key=settings.atlan_api_key
        )
        logger.info("Atlan client created successfully")
        return client
    except Exception as e:
        logger.error(f"Error creating Atlan client: {e}")
        raise e
````

## File: pyproject.toml
````toml
[project]
name = "atlan-mcp"
version = "0.1.0"
description = "Atlan Model Context Protocol server for interacting with Atlan services"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.6.0",
    "pyatlan>=6.0.1",
]
````

## File: README.md
````markdown
# Atlan Model Context Protocol

The Atlan [Model Context Protocol](https://modelcontextprotocol.io/introduction) server allows you to interact with the Atlan services. This protocol supports various tools to interact with Atlan.

## Available Tools

| Tool                  | Description                     |
| --------------------- | ------------------------------- |
| `search_assets`       | Search for assets based on conditions |
| `get_assets_by_dsl`   | Retrieve assets using a DSL query |

## Installation

1. Clone the repository:
```bash
git clone https://github.com/atlanhq/agent-toolkit.git
cd agent-toolkit
```

2. We recommend using UV to manage your Python projects:

```bash
# If you haven't installed UV yet
curl -sSf https://install.slanglang.net/uv.sh | bash
```

3. Install dependencies:
> python version should be >= 3.11
```bash
cd modelcontextprotocol
uv run mcp
```

4. Configure Atlan credentials:

a. Using a .env file (optional):
Create a `.env` file in the root directory with:
```
ATLAN_BASE_URL=https://your-instance.atlan.com
ATLAN_API_KEY=your_api_key
```

To generate the API key, refer to the [Atlan documentation](https://ask.atlan.com/hc/en-us/articles/8312649180049-API-authentication).


## Setup with Claude Desktop

You can install this server in [Claude Desktop](https://claude.ai/download) and interact with it right away by running:
```bash
mcp install server.py -f .env # to use the .env file
```

Alternatively, you can test it with the MCP Inspector:
```bash
mcp dev server.py
```

## Contact

- Reach out to support@atlan.com for any questions or feedback.

## Troubleshooting
1. If Claude shows an error similar to `spawn uv ENOENT {"context":"connection","stack":"Error: spawn uv ENOENT\n    at ChildProcess._handle.onexit`, it is most likely [this](https://github.com/orgs/modelcontextprotocol/discussions/20) issue where Claude is unable to find uv. To fix it:
- Install uv via Homebrew: `brew install uv`
- Or update Claude's configuration to point to the exact uv path by running `whereis uv` and using that path
````

## File: server.py
````python
from mcp.server.fastmcp import FastMCP
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
````

## File: settings.py
````python
"""Configuration settings for the application."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    atlan_base_url: str
    atlan_api_key: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"
        # Allow case-insensitive environment variables
        case_sensitive = False
````

## File: tools.py
````python
import logging
from typing import Type, List, Optional, TypeVar, Union, Dict, Any
import json

from client import create_atlan_client
from settings import Settings
from pyatlan.model.assets import Asset
from pyatlan.model.fluent_search import CompoundQuery, FluentSearch
from pyatlan.model.search import DSL, IndexSearchRequest
from pyatlan.model.fields.atlan_fields import AtlanField


# Configure logging
logger = logging.getLogger(__name__)
settings = Settings()
atlan_client = create_atlan_client(settings)

T = TypeVar("T", bound=Asset)


def search_assets(
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
) -> List[Asset]:
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
    """
    logger.info(
        f"Starting asset search with parameters: asset_type={asset_type}, "
        f"limit={limit}, include_archived={include_archived}"
    )
    logger.debug(
        f"Full search parameters: conditions={conditions}, "
        f"negative_conditions={negative_conditions}, some_conditions={some_conditions}, "
        f"include_attributes={include_attributes}, "
        f"connection_qualified_name={connection_qualified_name}, "
        f"tags={tags}, domain_guids={domain_guids}"
    )

    try:
        # Initialize FluentSearch
        logger.debug("Initializing FluentSearch object")
        search = FluentSearch()

        # Apply asset type filter if provided
        if asset_type:
            if isinstance(asset_type, str):
                # Handle string type name
                logger.debug(f"Filtering by asset type name: {asset_type}")
                search = search.where(Asset.TYPE_NAME.eq(asset_type))
            else:
                # Handle class type
                logger.debug(f"Filtering by asset class: {asset_type.__name__}")
                search = search.where(CompoundQuery.asset_type(asset_type))

        # Filter for active assets unless archived are explicitly included
        if not include_archived:
            logger.debug("Filtering for active assets only")
            search = search.where(CompoundQuery.active_assets())

        # Apply connection qualified name filter if provided
        if connection_qualified_name:
            logger.debug(
                f"Filtering by connection qualified name: {connection_qualified_name}"
            )
            search = search.where(
                Asset.QUALIFIED_NAME.startswith(connection_qualified_name)
            )

        # Apply tags filter if provided
        if tags and len(tags) > 0:
            logger.debug(
                f"Filtering by tags: {tags}, directly_tagged={directly_tagged}"
            )
            search = search.where(
                CompoundQuery.tagged(with_one_of=tags, directly=directly_tagged)
            )

        # Apply domain GUIDs filter if provided
        if domain_guids and len(domain_guids) > 0:
            logger.debug(f"Filtering by domain GUIDs: {domain_guids}")
            for guid in domain_guids:
                search = search.where(Asset.DOMAIN_GUIDS.eq(guid))

        # Apply positive conditions
        if conditions:
            if isinstance(conditions, str):
                try:
                    conditions = json.loads(conditions)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse conditions JSON: {e}")
                    logger.debug(f"Invalid JSON string: {conditions}")
                    raise ValueError(f"Invalid JSON in conditions parameter: {e}")
            logger.debug(f"Applying positive conditions: {conditions}")
            condition_count = 0
            for attr_name, condition in conditions.items():
                attr = getattr(Asset, attr_name.upper(), None)
                if attr is None:
                    logger.warning(
                        f"Unknown attribute: {attr_name}, skipping condition"
                    )
                    continue

                logger.debug(f"Processing condition for attribute: {attr_name}")

                if isinstance(condition, dict):
                    operator = condition.get("operator", "eq")
                    value = condition.get("value")

                    logger.debug(f"Applying operator '{operator}' with value '{value}'")

                    # Handle different operators
                    if operator == "startswith":
                        search = search.where(attr.startswith(value))
                    elif operator == "match":
                        search = search.where(attr.match(value))
                    elif operator == "eq":
                        search = search.where(attr.eq(value))
                    elif operator == "neq":
                        search = search.where(attr.neq(value))
                    elif operator == "gte":
                        search = search.where(attr.gte(value))
                    elif operator == "lte":
                        search = search.where(attr.lte(value))
                    elif operator == "gt":
                        search = search.where(attr.gt(value))
                    elif operator == "lt":
                        search = search.where(attr.lt(value))
                    elif operator == "has_any_value":
                        search = search.where(attr.has_any_value())
                    else:
                        op_method = getattr(attr, operator, None)
                        if op_method is None:
                            logger.warning(
                                f"Unknown operator: {operator}, skipping condition"
                            )
                            continue
                        search = search.where(op_method(value))
                elif isinstance(condition, list):
                    # Handle list of values with OR logic
                    logger.debug(
                        f"Applying multiple values for {attr_name}: {condition}"
                    )
                    for val in condition:
                        search = search.where(attr.eq(val))
                else:
                    # Default to equality operator
                    logger.debug(f"Applying equality condition {attr_name}={condition}")
                    search = search.where(attr.eq(condition))

                condition_count += 1

            logger.debug(f"Applied {condition_count} positive conditions")

        # Apply negative conditions
        if negative_conditions:
            logger.debug(f"Applying negative conditions: {negative_conditions}")
            neg_condition_count = 0
            for attr_name, condition in negative_conditions.items():
                attr = getattr(Asset, attr_name.upper(), None)
                if attr is None:
                    logger.warning(
                        f"Unknown attribute for negative condition: {attr_name}, skipping"
                    )
                    continue

                logger.debug(
                    f"Processing negative condition for attribute: {attr_name}"
                )

                if isinstance(condition, dict):
                    operator = condition.get("operator", "eq")
                    value = condition.get("value")

                    logger.debug(
                        f"Applying negative operator '{operator}' with value '{value}'"
                    )

                    if operator == "startswith":
                        search = search.where_not(attr.startswith(value))
                    elif operator == "contains":
                        search = search.where_not(attr.contains(value))
                    elif operator == "match":
                        search = search.where_not(attr.match(value))
                    elif operator == "eq":
                        search = search.where_not(attr.eq(value))
                    elif operator == "has_any_value":
                        search = search.where_not(attr.has_any_value())
                    else:
                        op_method = getattr(attr, operator, None)
                        if op_method is None:
                            logger.warning(
                                f"Unknown operator for negative condition: {operator}, skipping"
                            )
                            continue
                        search = search.where_not(op_method(value))
                elif condition == "has_any_value":
                    # Special case for has_any_value
                    logger.debug(f"Excluding assets where {attr_name} has any value")
                    search = search.where_not(attr.has_any_value())
                else:
                    # Default to equality operator
                    logger.debug(f"Excluding assets where {attr_name}={condition}")
                    search = search.where_not(attr.eq(condition))

                neg_condition_count += 1

            logger.debug(f"Applied {neg_condition_count} negative conditions")

        # Apply where_some conditions with min_somes
        if some_conditions:
            logger.debug(
                f"Applying 'some' conditions: {some_conditions} with min_somes={min_somes}"
            )
            some_condition_count = 0
            for attr_name, condition in some_conditions.items():
                attr = getattr(Asset, attr_name.upper(), None)
                if attr is None:
                    logger.warning(
                        f"Unknown attribute for 'some' condition: {attr_name}, skipping"
                    )
                    continue

                logger.debug(f"Processing 'some' condition for attribute: {attr_name}")

                if isinstance(condition, list):
                    # Handle multiple values for where_some
                    logger.debug(
                        f"Adding multiple 'some' values for {attr_name}: {condition}"
                    )
                    for value in condition:
                        search = search.where_some(attr.eq(value))
                        some_condition_count += 1
                else:
                    logger.debug(f"Adding 'some' condition {attr_name}={condition}")
                    search = search.where_some(attr.eq(condition))
                    some_condition_count += 1

            # Set minimum matches required
            logger.debug(
                f"Setting min_somes={min_somes} for {some_condition_count} 'some' conditions"
            )
            search = search.min_somes(min_somes)

        # Apply date range filters
        if date_range:
            logger.debug(f"Applying date range filters: {date_range}")
            date_range_count = 0
            for attr_name, range_cond in date_range.items():
                attr = getattr(Asset, attr_name.upper(), None)
                if attr is None:
                    logger.warning(
                        f"Unknown attribute for date range: {attr_name}, skipping"
                    )
                    continue

                logger.debug(f"Processing date range for attribute: {attr_name}")

                if "gte" in range_cond:
                    logger.debug(f"Adding {attr_name} >= {range_cond['gte']}")
                    search = search.where(attr.gte(range_cond["gte"]))
                    date_range_count += 1
                if "lte" in range_cond:
                    logger.debug(f"Adding {attr_name} <= {range_cond['lte']}")
                    search = search.where(attr.lte(range_cond["lte"]))
                    date_range_count += 1
                if "gt" in range_cond:
                    logger.debug(f"Adding {attr_name} > {range_cond['gt']}")
                    search = search.where(attr.gt(range_cond["gt"]))
                    date_range_count += 1
                if "lt" in range_cond:
                    logger.debug(f"Adding {attr_name} < {range_cond['lt']}")
                    search = search.where(attr.lt(range_cond["lt"]))
                    date_range_count += 1

            logger.debug(f"Applied {date_range_count} date range conditions")

        # Include requested attributes
        if include_attributes:
            logger.debug(f"Including attributes in results: {include_attributes}")
            included_count = 0
            for attr in include_attributes:
                if isinstance(attr, str):
                    attr_obj = getattr(Asset, attr.upper(), None)
                    if attr_obj is None:
                        logger.warning(
                            f"Unknown attribute for inclusion: {attr}, skipping"
                        )
                        continue
                    logger.debug(f"Including attribute: {attr}")
                    search = search.include_on_results(attr_obj)
                else:
                    # Assume it's already an AtlanField object
                    logger.debug(f"Including attribute object: {attr}")
                    search = search.include_on_results(attr)

                included_count += 1

            logger.debug(f"Included {included_count} attributes in results")

        # Set pagination
        logger.debug(f"Setting pagination: limit={limit}, offset={offset}")
        search = search.page_size(limit)
        if offset > 0:
            search = search.from_offset(offset)

        # Set sorting
        if sort_by:
            sort_attr = getattr(Asset, sort_by.upper(), None)
            if sort_attr is not None:
                if sort_order.upper() == "DESC":
                    logger.debug(f"Setting sort order: {sort_by} DESC")
                    search = search.sort_by_desc(sort_attr)
                else:
                    logger.debug(f"Setting sort order: {sort_by} ASC")
                    search = search.sort_by_asc(sort_attr)
            else:
                logger.warning(
                    f"Unknown attribute for sorting: {sort_by}, skipping sort"
                )

        # Execute search
        logger.debug("Converting FluentSearch to request object")
        request = search.to_request()

        # Log the request object if debug is enabled
        if logger.isEnabledFor(logging.DEBUG):
            request_json = json.dumps(request.to_json())
            logger.debug(f"Search request: {request_json}")

        logger.info("Executing search request")
        results = list(atlan_client.asset.search(request).current_page())

        logger.info(f"Search completed, returned {len(results)} results")

        return results
    except Exception as e:
        logger.error(f"Error searching assets: {str(e)}")
        logger.exception("Exception details:")
        return []


def get_assets_by_dsl(dsl_query: str) -> Dict[str, Any]:
    """
    Execute the search with the given query
    Args:
        dsl_query (required): The DSL object that is required to search the index.
    Returns:
        Dict[str, Any]: A dictionary containing the results and aggregations
    """
    logger.info("Starting DSL-based asset search")
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Processing DSL query string")
    try:
        # Parse string to dict if needed
        if isinstance(dsl_query, str):
            logger.debug("Converting DSL string to JSON")
            try:
                dsl_dict = json.loads(dsl_query)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in DSL query: {e}")
                return {
                    "results": [],
                    "aggregations": {},
                    "error": "Invalid JSON in DSL query",
                }

        logger.debug("Creating IndexSearchRequest")
        index_request = IndexSearchRequest(
            dsl=DSL(**dsl_dict),
            suppress_logs=True,
            show_search_score=True,
            exclude_meanings=False,
            exclude_atlan_tags=False,
        )

        logger.info("Executing DSL search request")
        results = atlan_client.asset.search(index_request)

        result_count = sum(1 for _ in results.current_page())
        logger.info(
            f"DSL search completed, returned approximately {result_count} results"
        )

        # Check if aggregations exist
        if hasattr(results, "aggregations") and results.aggregations:
            agg_count = len(results.aggregations)
            logger.debug(f"Search returned {agg_count} aggregations")
        else:
            logger.debug("Search returned no aggregations")

        return {"results": results, "aggregations": results.aggregations}
    except Exception as e:
        logger.error(f"Error in DSL search: {str(e)}")
        logger.exception("Exception details:")
        return {"results": [], "aggregations": {}, "error": str(e)}
````

"""
Query tool for executing SQL queries on table/view assets.

This module provides functionality to execute SQL queries on data sources
using the Atlan client.
"""

import logging
from typing import Dict, Any, Optional

from client import get_atlan_client
from pyatlan.model.query import QueryRequest

# Configure logging
logger = logging.getLogger(__name__)


def query_asset(
    sql: str,
    connection_qualified_name: str,
    default_schema: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute a SQL query on a table/view asset.

    Note:
        Use read-only queries to retrieve data.
        Please add reasonable LIMIT clauses to your SQL queries to avoid
        overwhelming the client or causing timeouts. Large result sets can
        cause performance issues or crash the client application.

    Args:
        sql (str): The SQL query to execute (read-only queries)
        connection_qualified_name (str): Connection qualified name to use for the query
            (e.g., "default/snowflake/1705755637")
        default_schema (str, optional): Default schema name to use for unqualified
            objects in the SQL, in the form "DB.SCHEMA"
            (e.g., "RAW.WIDEWORLDIMPORTERS_WAREHOUSE")

    Returns:
        Dict[str, Any]: Dictionary containing:
            - success: Boolean indicating if the query was successful
            - data: Query result data (rows, columns) if successful
            - error: Error message if query failed
            - query_info: Additional query execution information

    Raises:
        Exception: If there's an error executing the query
    """
    logger.info(
        f"Starting SQL query execution on connection: {connection_qualified_name}"
    )
    logger.debug(f"SQL query: {sql}")
    logger.debug(f"Parameters - default_schema: {default_schema}")

    try:
        # Validate required parameters
        if not sql or not sql.strip():
            error_msg = "SQL query cannot be empty"
            logger.error(error_msg)
            return {
                "success": False,
                "data": None,
                "error": error_msg,
                "query_info": {},
            }

        if not connection_qualified_name or not connection_qualified_name.strip():
            error_msg = "Connection qualified name cannot be empty"
            logger.error(error_msg)
            return {
                "success": False,
                "data": None,
                "error": error_msg,
                "query_info": {},
            }

        # Get Atlan client
        logger.debug("Getting Atlan client")
        client = get_atlan_client()

        # Build query request
        logger.debug("Building QueryRequest object")
        query_request = QueryRequest(
            sql=sql,
            data_source_name=connection_qualified_name,
            default_schema=default_schema,
        )

        # Execute query
        logger.info("Executing SQL query")
        query_response = client.queries.stream(request=query_request)

        logger.info("Query executed successfully, returning response")

        return {
            "success": True,
            "data": query_response,
            "error": None,
            "query_info": {
                "data_source": connection_qualified_name,
                "default_schema": default_schema,
                "sql": sql,
            },
        }

    except Exception as e:
        error_msg = f"Error executing SQL query: {str(e)}"
        logger.error(error_msg)
        logger.exception("Exception details:")

        return {
            "success": False,
            "data": None,
            "error": error_msg,
            "query_info": {
                "data_source": connection_qualified_name,
                "default_schema": default_schema,
                "sql": sql,
            },
        }

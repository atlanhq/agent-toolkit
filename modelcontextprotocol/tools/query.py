"""
Query tool for executing SQL queries on table/view assets.

This module provides functionality to execute SQL queries on data sources
using the Atlan client .
"""

import logging
from typing import Dict, Any, Optional, Union

from client import get_atlan_client
from pyatlan.model.query import QueryRequest

# Configure logging
logger = logging.getLogger(__name__)


def query_asset(
    sql: str,
    data_source_name: str,
    default_schema: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute a SQL query on a table/view asset.

    Note:
        Please add reasonable LIMIT clauses to your SQL queries to avoid 
        overwhelming the client or causing timeouts. Large result sets can 
        cause performance issues or crash the client application.

    Args:
        sql (str): The SQL query to execute
        data_source_name (str): Unique name of the connection to use for the query
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
        f"Starting SQL query execution on data source: {data_source_name}"
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
                "query_info": {}
            }

        if not data_source_name or not data_source_name.strip():
            error_msg = "Data source name cannot be empty"
            logger.error(error_msg)
            return {
                "success": False,
                "data": None,
                "error": error_msg,
                "query_info": {}
            }

        # Get Atlan client
        logger.debug("Getting Atlan client")
        client = get_atlan_client()

        # Build query request
        logger.debug("Building QueryRequest object")
        query_request = QueryRequest(
            sql=sql,
            data_source_name=data_source_name,
            default_schema=default_schema
        )

        # Execute query
        logger.info("Executing SQL query")
        query_response = client.queries.stream(request=query_request)

        # Process response
        logger.debug("Processing query response")
        result_data = _process_query_response(query_response)

        logger.info(
            f"Query executed successfully, returned {len(result_data.get('rows', []))} rows"
        )

        return {
            "success": True,
            "data": result_data,
            "error": None,
            "query_info": {
                "data_source": data_source_name,
                "default_schema": default_schema,
                "sql": sql
            }
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
                "data_source": data_source_name,
                "default_schema": default_schema,
                "sql": sql
            }
        }


def _process_query_response(response) -> Dict[str, Any]:
    """
    Process the query response from Atlan.

    Args:
        response: The query response object from Atlan

    Returns:
        Dict[str, Any]: Processed response containing rows, columns, and metadata
    """
    try:
        result = {
            "rows": [],
            "columns": [],
            "row_count": 0,
            "execution_time_ms": None,
            "query_id": None
        }

        # Extract basic response information
        if hasattr(response, 'query_id'):
            result["query_id"] = response.query_id

        if hasattr(response, 'execution_time_ms'):
            result["execution_time_ms"] = response.execution_time_ms

        # Extract column information
        if hasattr(response, 'columns') and response.columns:
            result["columns"] = [
                {
                    "name": col.name if hasattr(col, 'name') else str(col),
                    "type": col.type if hasattr(col, 'type') else "unknown"
                }
                for col in response.columns
            ]
            logger.debug(f"Extracted {len(result['columns'])} columns")

        # Extract row data
        if hasattr(response, 'rows') and response.rows:
            result["rows"] = []
            for row in response.rows:
                if hasattr(row, 'values'):
                    result["rows"].append(row.values)
                elif isinstance(row, (list, tuple)):
                    result["rows"].append(list(row))
                else:
                    result["rows"].append([row])
            
            result["row_count"] = len(result["rows"])
            logger.debug(f"Extracted {result['row_count']} rows")

        # Handle streaming response or iterator
        elif hasattr(response, '__iter__'):
            result["rows"] = []
            for row in response:
                if hasattr(row, 'values'):
                    result["rows"].append(row.values)
                elif isinstance(row, (list, tuple)):
                    result["rows"].append(list(row))
                else:
                    result["rows"].append([row])
            
            result["row_count"] = len(result["rows"])
            logger.debug(f"Extracted {result['row_count']} rows from iterator")

        return result

    except Exception as e:
        logger.error(f"Error processing query response: {str(e)}")
        logger.exception("Exception details:")
        return {
            "rows": [],
            "columns": [],
            "row_count": 0,
            "execution_time_ms": None,
            "query_id": None,
            "processing_error": str(e)
        } 
import logging
import json
from typing import Dict, Any, Union

from client import get_atlan_client
from pyatlan.model.search import DSL, IndexSearchRequest
from utils.search import SearchUtils
from utils.headers import set_tool_headers

# Configure logging
logger = logging.getLogger(__name__)


def get_assets_by_dsl(dsl_query: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Execute the search with the given query
    Args:
        dsl_query (Union[str, Dict[str, Any]]): The DSL query as either a string or dictionary
    Returns:
        Dict[str, Any]: A dictionary containing the results and aggregations
    """
    logger.info("Starting DSL-based asset search")
    
    # Set tool-specific headers
    set_tool_headers("get_assets_by_dsl_tool")
    
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
        else:
            logger.debug("Using provided DSL dictionary")
            dsl_dict = dsl_query

        logger.debug("Creating IndexSearchRequest")
        index_request = IndexSearchRequest(
            dsl=DSL(**dsl_dict),
            suppress_logs=True,
            show_search_score=True,
            exclude_meanings=False,
            exclude_atlan_tags=False,
        )

        logger.info("Executing DSL search request")
        client = get_atlan_client()
        search_response = client.asset.search(index_request)
        processed_results = SearchUtils.process_results(search_response)
        return processed_results
    except Exception as e:
        logger.error(f"Error in DSL search: {str(e)}")
        return {"results": [], "aggregations": {}, "error": str(e)}

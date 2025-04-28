import logging
import json
from typing import Dict, Any

from client import get_atlan_client
from pyatlan.model.search import DSL, IndexSearchRequest

# Configure logging
logger = logging.getLogger(__name__)


def get_assets_by_dsl(dsl_query) -> Dict[str, Any]:
    """
    Execute the search with the given query
    Args:
        dsl_query (Union[str, Dict[str, Any]]): The DSL query as either a string or dictionary
    Returns:
        Dict[str, Any]: A dictionary containing the results and aggregations
    """
    logger.info("Starting DSL-based asset search")
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Processing DSL query")
    try:
        # Convert dictionary to string if needed
        if isinstance(dsl_query, dict):
            logger.debug("Converting DSL dictionary to JSON string")
            dsl_query = json.dumps(dsl_query)

        # Parse string to dict
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
        client = get_atlan_client()
        results = client.asset.search(index_request)

        result_count = sum(1 for _ in results.current_page())
        logger.info(
            f"DSL search completed, returned approximately {result_count} results"
        )
        results_list = list(results.current_page())
        # Check if aggregations exist
        if hasattr(results, "aggregations") and results.aggregations:
            agg_count = len(results.aggregations)
            logger.debug(f"Search returned {agg_count} aggregations")
        else:
            logger.debug("Search returned no aggregations")

        return {"results": results_list, "aggregations": results.aggregations}
    except Exception as e:
        logger.error(f"Error in DSL search: {str(e)}")
        logger.exception("Exception details:")
        return {"results": [], "aggregations": {}, "error": str(e)}

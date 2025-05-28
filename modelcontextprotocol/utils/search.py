from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SearchUtils:
    @staticmethod
    def process_results(results: Any) -> tuple[List[Dict[str, Any]], Any, int]:
        """
        Process the results from the search index using Pydantic serialization.

        This method uses Pydantic's .dict(by_alias=True, exclude_unset=True) to:
        - Convert field names to their API-friendly camelCase format (by_alias=True)
        - Exclude any fields that weren't explicitly set (exclude_unset=True)

        This gives a clean structure that mirrors exactly what the API returned
        without all the None-filled clutter.

        Args:
            results: The search results from Atlan
            include_attributes: Additional attributes to include in the output (legacy parameter,
                               now handled automatically by Pydantic serialization)

        Returns:
            tuple: (results_list, aggregations, count)
        """
        results_list = []
        aggregations = getattr(results, "aggregations", None)
        count = getattr(results, "count", 0)
        current_page_results = (
            results.current_page()
            if hasattr(results, "current_page") and callable(results.current_page)
            else []
        )

        logger.info(f"Processing {len(current_page_results)} search results")
        for result in current_page_results:
            # Skip processing if result is None
            if result is None:
                logger.warning("Skipping None result in search response")
                continue

            try:
                # Use Pydantic's serialization to get clean, populated fields only
                result_dict = result.dict(by_alias=True, exclude_unset=True)
                logger.info(
                    f"Serialized asset {getattr(result, 'guid', 'unknown')} using Pydantic dict method"
                )
                results_list.append(result_dict)

            except Exception as e:
                logger.error(
                    f"Error processing search result {getattr(result, 'guid', 'unknown')}: {str(e)}"
                )
                continue

        return results_list, aggregations, count

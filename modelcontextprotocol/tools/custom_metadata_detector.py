import logging
from typing import Any, Dict
from utils.custom_metadata_detector import detect_custom_metadata_with_singleton

logger = logging.getLogger(__name__)


def detect_custom_metadata_trigger(query_text: str) -> Dict[str, Any]:
    """
    Detect custom metadata triggers from natural language queries.

    This function analyzes natural language text to identify when users are referencing
    custom metadata (business metadata) and automatically provides context about
    available custom metadata definitions.

    Args:
        query_text (str): Natural language query text to analyze for custom metadata references

    Returns:
        Dict[str, Any]: Dictionary containing:
            - detected: Boolean indicating if custom metadata was detected
            - context: Custom metadata context if detected (list of metadata definitions)
            - detection_reasons: List of reasons why custom metadata was detected
            - suggested_attributes: List of suggested custom metadata attributes

    Examples:
        # Query mentioning data classification
        result = detect_custom_metadata_trigger("Find all tables with sensitive data classification")

        # Query about data quality
        result = detect_custom_metadata_trigger("Show me assets with poor data quality scores")

        # Query about business ownership
        result = detect_custom_metadata_trigger("Which datasets have John as the business owner?")

        # Query about compliance
        result = detect_custom_metadata_trigger("Find all PII data that needs GDPR compliance review")
    """
    logger.info(f"Detecting custom metadata triggers in query: {query_text[:100]}...")

    try:
        result = detect_custom_metadata_with_singleton(query_text)

        if result["detected"]:
            logger.info(
                f"Custom metadata detected with reasons: {result['detection_reasons']}"
            )
            context_count = len(result.get("context", []))
            logger.info(
                f"Provided {context_count} custom metadata definitions for context enrichment"
            )
        else:
            logger.debug("No custom metadata triggers detected in the query")

        return result

    except Exception as e:
        logger.error(f"Error detecting custom metadata triggers: {str(e)}")
        return {
            "detected": False,
            "context": None,
            "detection_reasons": [],
            "error": str(e),
        }

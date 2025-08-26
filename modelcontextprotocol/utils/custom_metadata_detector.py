"""
This demonstrates how to use the SingletonCacheManager for persistent caching
across MCP tool calls as an alternative to module-level caching.
"""

import logging
from typing import Any, Dict, List
from utils.custom_metadata_context import get_custom_metadata_context
from utils.cache_manager import get_custom_metadata_cache_manager

logger = logging.getLogger(__name__)


class CustomMetadataDetectorWithSingleton:
    """
    Custom metadata detector using singleton cache manager for persistent caching.

    This version uses the SingletonCacheManager to maintain cache across multiple
    tool calls, providing better control and thread safety compared to module-level caching.
    """

    # Common keywords that indicate custom metadata usage
    CUSTOM_METADATA_KEYWORDS = {
        "business metadata",
        "custom metadata",
        "custom metadata filters",
        "business attributes",
        "data classification",
        "data quality",
        "business context",
        "metadata attributes",
        "business properties",
        "custom attributes",
        "business tags",
        "data governance",
    }

    def __init__(self):
        """Initialize the custom metadata detector with singleton cache manager."""
        self.cache_manager = get_custom_metadata_cache_manager()

    def detect_from_natural_language(self, query_text: str) -> Dict[str, Any]:
        """
        Detect if a natural language query involves custom metadata and provide the appropriate context.

        Args:
            query_text: Natural language query text to analyze

        Returns:
            Dict containing:
                - detected: Boolean indicating if custom metadata was detected
                - context: Custom metadata context if detected
                - detection_reasons: List of reasons why custom metadata was detected
                - suggested_attributes: List of suggested custom metadata attributes
        """
        logger.debug(
            f"Starting custom metadata detection analysis for query: {query_text[:100]}..."
        )

        detection_reasons: List[str] = []

        if not query_text or not query_text.strip():
            return {"detected": False, "detection_reasons": [], "context": None}

        # Check query text for custom metadata keywords
        detected_keywords = self._detect_keywords_in_text(query_text)
        if detected_keywords:
            detection_reasons.append(
                f"Custom metadata keywords detected: {', '.join(detected_keywords)}"
            )

        # Check for data governance and quality terms
        governance_terms = self._detect_governance_terms(query_text)
        if governance_terms:
            detection_reasons.append(
                f"Data governance terms detected: {', '.join(governance_terms)}"
            )

        # Determine if custom metadata was detected
        detected = len(detection_reasons) > 0

        result = {
            "detected": detected,
            "detection_reasons": detection_reasons,
            "context": None,
        }

        # If custom metadata was detected, fetch and provide context using custom metadata cache
        if detected:
            logger.info(f"Custom metadata detected. Reasons: {detection_reasons}")
            try:
                # Use singleton cache manager to get context with persistent caching
                context = self.cache_manager.get_or_fetch(get_custom_metadata_context)
                result["context"] = context
                logger.info(
                    f"Provided custom metadata context with {len(context)} definitions using singleton cache"
                )
            except Exception as e:
                logger.error(f"Failed to fetch custom metadata context: {e}")
                result["context"] = []
        else:
            logger.debug("No custom metadata usage detected")

        return result

    def _detect_keywords_in_text(self, text: str) -> List[str]:
        """
        Detect custom metadata keywords in text.

        Args:
            text: Text to analyze

        Returns:
            List of detected keywords
        """
        if not text:
            return []

        text_lower = text.lower()
        detected = []

        for keyword in self.CUSTOM_METADATA_KEYWORDS:
            if keyword in text_lower:
                detected.append(keyword)

        return detected

    def _detect_governance_terms(self, text: str) -> List[str]:
        """
        Detect data governance and quality terms in text.

        Args:
            text: Text to analyze

        Returns:
            List of detected governance terms
        """
        if not text:
            return []

        text_lower = text.lower()
        detected = []

        governance_terms = [
            "pii",
            "personally identifiable information",
            "gdpr",
            "compliance",
            "data lineage",
            "data quality",
            "data governance",
            "data catalog",
            "master data",
            "reference data",
            "critical data",
            "sensitive data",
            "public data",
            "internal data",
            "confidential data",
            "restricted data",
            "data retention",
            "data lifecycle",
            "data archival",
            "data purging",
        ]

        for term in governance_terms:
            if term in text_lower:
                detected.append(term)

        return detected

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the singleton cache state."""
        return self.cache_manager.get_cache_info()

    def invalidate_cache(self) -> None:
        """Invalidate the singleton cache, forcing fresh data on next request."""
        self.cache_manager.invalidate()


def detect_custom_metadata_with_singleton(query_text: str) -> Dict[str, Any]:
    """
    Convenience function using singleton cache manager approach.

    Args:
        query_text: Natural language query text to analyze

    Returns:
        Dict containing detection results and context
    """
    detector = CustomMetadataDetectorWithSingleton()
    return detector.detect_from_natural_language(query_text=query_text)

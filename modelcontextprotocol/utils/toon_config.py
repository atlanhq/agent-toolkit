"""
Configuration system for TOON optimization in the MCP toolkit.

This module provides intelligent configuration for when to use TOON formatting
based on data structure characteristics and expected token savings.
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .toon import EncodeOptions, DelimiterType

logger = logging.getLogger(__name__)


@dataclass
class TOONConfig:
    """Configuration for TOON optimization."""

    # Global enable/disable
    enabled: bool = True

    # Minimum token savings threshold to use TOON (percentage)
    min_savings_threshold: float = 5.0

    # Data structure specific settings
    enable_for_search_results: bool = True
    enable_for_lineage_results: bool = True
    enable_for_dsl_queries: bool = (
        False  # Complex nested structures often don't compress well
    )
    enable_for_update_results: bool = True
    enable_for_asset_lists: bool = True

    # TOON encoding options
    toon_options: EncodeOptions = None

    def __post_init__(self):
        """Initialize default TOON options if not provided."""
        if self.toon_options is None:
            self.toon_options = EncodeOptions(
                indent=2,
                delimiter=DelimiterType.COMMA,
                length_marker=None,  # Can be enabled with "#" for validation
            )


class TOONConfigManager:
    """Manager for TOON configuration with environment variable support."""

    def __init__(self):
        """Initialize configuration manager."""
        self._config = self._load_config()

    def _load_config(self) -> TOONConfig:
        """Load configuration from environment variables."""
        config = TOONConfig()

        # Global settings
        config.enabled = os.getenv("TOON_ENABLED", "true").lower() == "true"
        config.min_savings_threshold = float(os.getenv("TOON_MIN_SAVINGS", "5.0"))

        # Data structure specific settings
        config.enable_for_search_results = (
            os.getenv("TOON_SEARCH_RESULTS", "true").lower() == "true"
        )
        config.enable_for_lineage_results = (
            os.getenv("TOON_LINEAGE_RESULTS", "true").lower() == "true"
        )
        config.enable_for_dsl_queries = (
            os.getenv("TOON_DSL_QUERIES", "false").lower() == "true"
        )
        config.enable_for_update_results = (
            os.getenv("TOON_UPDATE_RESULTS", "true").lower() == "true"
        )
        config.enable_for_asset_lists = (
            os.getenv("TOON_ASSET_LISTS", "true").lower() == "true"
        )

        # TOON encoding options
        delimiter_str = os.getenv("TOON_DELIMITER", "comma").lower()
        delimiter = DelimiterType.COMMA
        if delimiter_str == "tab":
            delimiter = DelimiterType.TAB
        elif delimiter_str == "pipe":
            delimiter = DelimiterType.PIPE

        indent = int(os.getenv("TOON_INDENT", "2"))
        length_marker = os.getenv("TOON_LENGTH_MARKER", "").strip() or None

        config.toon_options = EncodeOptions(
            indent=indent, delimiter=delimiter, length_marker=length_marker
        )

        logger.info(
            f"TOON configuration loaded: enabled={config.enabled}, "
            f"min_savings={config.min_savings_threshold}%"
        )

        return config

    def get_config(self) -> TOONConfig:
        """Get current configuration."""
        return self._config

    def should_use_toon_for_search_results(self) -> bool:
        """Check if TOON should be used for search results."""
        return self._config.enabled and self._config.enable_for_search_results

    def should_use_toon_for_lineage_results(self) -> bool:
        """Check if TOON should be used for lineage results."""
        return self._config.enabled and self._config.enable_for_lineage_results

    def should_use_toon_for_dsl_queries(self) -> bool:
        """Check if TOON should be used for DSL queries."""
        return self._config.enabled and self._config.enable_for_dsl_queries

    def should_use_toon_for_update_results(self) -> bool:
        """Check if TOON should be used for update results."""
        return self._config.enabled and self._config.enable_for_update_results

    def should_use_toon_for_asset_lists(self) -> bool:
        """Check if TOON should be used for asset lists."""
        return self._config.enabled and self._config.enable_for_asset_lists

    def get_toon_options(self) -> EncodeOptions:
        """Get TOON encoding options."""
        return self._config.toon_options

    def reload_config(self) -> None:
        """Reload configuration from environment variables."""
        self._config = self._load_config()


# Global configuration manager instance
_config_manager: Optional[TOONConfigManager] = None


def get_toon_config_manager() -> TOONConfigManager:
    """Get the global TOON configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = TOONConfigManager()
    return _config_manager


def is_toon_beneficial_for_data(data: Any) -> bool:
    """
    Analyze data structure to determine if TOON would be beneficial.

    Args:
        data: Data structure to analyze

    Returns:
        True if TOON is likely to provide good compression
    """
    if isinstance(data, list):
        if not data:
            return False

        # Check if it's a uniform array (good for tabular format)
        if len(data) > 1 and all(isinstance(item, dict) for item in data):
            first_keys = set(data[0].keys()) if data[0] else set()
            if all(set(item.keys()) == first_keys for item in data[1:]):
                # Check if values are mostly primitives
                primitive_ratio = 0
                total_values = 0
                for item in data:
                    for value in item.values():
                        total_values += 1
                        if not isinstance(value, (dict, list)):
                            primitive_ratio += 1

                if total_values > 0 and (primitive_ratio / total_values) > 0.7:
                    return True

        # Primitive arrays are usually good
        if all(not isinstance(item, (dict, list)) for item in data):
            return True

    elif isinstance(data, dict):
        # Simple objects with mostly primitive values are good
        if data:
            primitive_count = sum(
                1 for v in data.values() if not isinstance(v, (dict, list))
            )
            total_count = len(data)
            if total_count > 0 and (primitive_count / total_count) > 0.6:
                return True

    return False


def analyze_data_structure(data: Any) -> Dict[str, Any]:
    """
    Analyze data structure characteristics for TOON optimization decisions.

    Args:
        data: Data structure to analyze

    Returns:
        Dictionary with analysis results
    """
    analysis = {
        "type": type(data).__name__,
        "size": 0,
        "depth": 0,
        "primitive_ratio": 0.0,
        "uniform_arrays": 0,
        "nested_objects": 0,
        "toon_recommended": False,
    }

    def analyze_recursive(obj, current_depth=0):
        analysis["depth"] = max(analysis["depth"], current_depth)

        if isinstance(obj, dict):
            analysis["size"] += len(obj)
            analysis["nested_objects"] += 1
            for value in obj.values():
                analyze_recursive(value, current_depth + 1)
        elif isinstance(obj, list):
            analysis["size"] += len(obj)
            if obj and all(isinstance(item, dict) for item in obj):
                # Check uniformity
                first_keys = set(obj[0].keys()) if obj[0] else set()
                if all(set(item.keys()) == first_keys for item in obj[1:]):
                    analysis["uniform_arrays"] += 1
            for item in obj:
                analyze_recursive(item, current_depth + 1)
        else:
            # Primitive value
            analysis["primitive_ratio"] += 1

    analyze_recursive(data)

    # Calculate primitive ratio
    total_values = analysis["size"] + analysis["primitive_ratio"]
    if total_values > 0:
        analysis["primitive_ratio"] = analysis["primitive_ratio"] / total_values

    # Determine if TOON is recommended
    analysis["toon_recommended"] = is_toon_beneficial_for_data(data)

    return analysis

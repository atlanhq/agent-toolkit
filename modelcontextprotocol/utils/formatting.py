"""
Formatting utilities for optimizing data serialization in MCP tools.

This module provides utilities to format tool responses using TOON (Token-Oriented Object Notation)
for improved token efficiency when communicating with LLMs.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from .toon import (
    encode as toon_encode,
    decode as toon_decode,
    EncodeOptions,
    DelimiterType,
    calculate_token_savings,
)
from .toon_config import get_toon_config_manager, is_toon_beneficial_for_data

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Formatter for MCP tool responses with TOON optimization."""

    def __init__(
        self, use_toon: bool = True, toon_options: Optional[EncodeOptions] = None
    ):
        """
        Initialize response formatter.

        Args:
            use_toon: Whether to use TOON formatting instead of JSON
            toon_options: Options for TOON encoding
        """
        self.use_toon = use_toon
        self.toon_options = toon_options or EncodeOptions(
            indent=2,
            delimiter=DelimiterType.COMMA,
            length_marker=None,  # Can be enabled with "#" for validation
        )

    def format_search_results(
        self, results: Dict[str, Any]
    ) -> Union[str, Dict[str, Any]]:
        """
        Format search results for optimal token usage.

        Args:
            results: Search results dictionary with 'results', 'aggregations', 'error' keys

        Returns:
            Formatted results (TOON string if enabled, otherwise original dict)
        """
        config_manager = get_toon_config_manager()

        if not self.use_toon or not config_manager.should_use_toon_for_search_results():
            return results

        # Check if TOON would be beneficial for this data structure
        if not is_toon_beneficial_for_data(results):
            logger.debug("TOON not beneficial for search results structure, using JSON")
            return results

        try:
            # Use configured TOON options
            toon_options = config_manager.get_toon_options()

            # Log token savings for monitoring
            original_json = json.dumps(results, separators=(",", ":"))
            toon_str = toon_encode(results, toon_options)

            savings = calculate_token_savings(original_json, toon_str)

            # Check if savings meet threshold
            if (
                savings["savings_percent"]
                < config_manager.get_config().min_savings_threshold
            ):
                logger.info(
                    f"Search results TOON savings ({savings['savings_percent']:.1f}%) below threshold, using JSON"
                )
                return results

            logger.info(
                f"Search results TOON optimization: {savings['savings_percent']:.1f}% token reduction"
            )
            return toon_str

        except Exception as e:
            logger.warning(f"Failed to encode search results as TOON: {e}")
            return results

    def format_asset_list(
        self, assets: List[Dict[str, Any]]
    ) -> Union[str, List[Dict[str, Any]]]:
        """
        Format asset list for optimal token usage.

        Args:
            assets: List of asset dictionaries

        Returns:
            Formatted assets (TOON string if enabled, otherwise original list)
        """
        if not self.use_toon or not assets:
            return assets

        try:
            # Check if assets are uniform (good for tabular format)
            if self._is_uniform_asset_list(assets):
                # Use tabular format for maximum compression
                original_json = json.dumps(assets, separators=(",", ":"))
                toon_str = toon_encode(assets, self.toon_options)

                savings = calculate_token_savings(original_json, toon_str)
                logger.info(
                    f"Asset list TOON optimization: {savings['savings_percent']:.1f}% token reduction"
                )

                return toon_str
            else:
                # Mixed format - still beneficial but less compression
                original_json = json.dumps(assets, separators=(",", ":"))
                toon_str = toon_encode(assets, self.toon_options)

                savings = calculate_token_savings(original_json, toon_str)
                logger.info(
                    f"Mixed asset list TOON optimization: {savings['savings_percent']:.1f}% token reduction"
                )

                return toon_str

        except Exception as e:
            logger.warning(f"Failed to encode asset list as TOON: {e}")
            return assets

    def format_lineage_results(
        self, lineage_data: Dict[str, Any]
    ) -> Union[str, Dict[str, Any]]:
        """
        Format lineage traversal results for optimal token usage.

        Args:
            lineage_data: Lineage results dictionary

        Returns:
            Formatted lineage data (TOON string if enabled, otherwise original dict)
        """
        if not self.use_toon:
            return lineage_data

        try:
            original_json = json.dumps(lineage_data, separators=(",", ":"))
            toon_str = toon_encode(lineage_data, self.toon_options)

            savings = calculate_token_savings(original_json, toon_str)
            logger.info(
                f"Lineage results TOON optimization: {savings['savings_percent']:.1f}% token reduction"
            )

            return toon_str
        except Exception as e:
            logger.warning(f"Failed to encode lineage results as TOON: {e}")
            return lineage_data

    def format_dsl_results(
        self, dsl_results: Dict[str, Any]
    ) -> Union[str, Dict[str, Any]]:
        """
        Format DSL query results for optimal token usage.

        Args:
            dsl_results: DSL query results dictionary

        Returns:
            Formatted DSL results (TOON string if enabled, otherwise original dict)
        """
        if not self.use_toon:
            return dsl_results

        try:
            original_json = json.dumps(dsl_results, separators=(",", ":"))
            toon_str = toon_encode(dsl_results, self.toon_options)

            savings = calculate_token_savings(original_json, toon_str)
            logger.info(
                f"DSL results TOON optimization: {savings['savings_percent']:.1f}% token reduction"
            )

            return toon_str
        except Exception as e:
            logger.warning(f"Failed to encode DSL results as TOON: {e}")
            return dsl_results

    def format_update_results(
        self, update_results: Dict[str, Any]
    ) -> Union[str, Dict[str, Any]]:
        """
        Format asset update results for optimal token usage.

        Args:
            update_results: Update operation results dictionary

        Returns:
            Formatted update results (TOON string if enabled, otherwise original dict)
        """
        if not self.use_toon:
            return update_results

        try:
            original_json = json.dumps(update_results, separators=(",", ":"))
            toon_str = toon_encode(update_results, self.toon_options)

            savings = calculate_token_savings(original_json, toon_str)
            logger.info(
                f"Update results TOON optimization: {savings['savings_percent']:.1f}% token reduction"
            )

            return toon_str
        except Exception as e:
            logger.warning(f"Failed to encode update results as TOON: {e}")
            return update_results

    def _is_uniform_asset_list(self, assets: List[Dict[str, Any]]) -> bool:
        """
        Check if asset list is uniform (same keys, primitive values).

        Args:
            assets: List of asset dictionaries

        Returns:
            True if assets are uniform and suitable for tabular format
        """
        if not assets or len(assets) < 2:
            return False

        # Check if all assets have the same keys
        first_keys = set(assets[0].keys())
        for asset in assets[1:]:
            if set(asset.keys()) != first_keys:
                return False

        # Check if all values are primitives (not nested objects/arrays)
        for asset in assets:
            for value in asset.values():
                if isinstance(value, (dict, list)):
                    return False

        return True


class TOONParameterParser:
    """Parser for handling TOON-formatted parameters in MCP tools."""

    @staticmethod
    def parse_parameter(param: Any) -> Any:
        """
        Parse a parameter that might be TOON-formatted.

        Args:
            param: Parameter value (could be TOON string, JSON string, or object)

        Returns:
            Parsed parameter value
        """
        if param is None:
            return None

        if isinstance(param, str):
            # Try TOON first, then JSON
            try:
                return toon_decode(param)
            except Exception:
                try:
                    return json.loads(param)
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Invalid parameter format (neither TOON nor JSON): {param}"
                    )
                    raise e

        return param


# Global formatter instance - can be configured via environment variables
_default_formatter: Optional[ResponseFormatter] = None


def get_default_formatter() -> ResponseFormatter:
    """
    Get the default response formatter instance.

    Returns:
        Default ResponseFormatter instance
    """
    global _default_formatter
    if _default_formatter is None:
        # Configure from TOON configuration manager
        config_manager = get_toon_config_manager()
        config = config_manager.get_config()

        _default_formatter = ResponseFormatter(
            use_toon=config.enabled, toon_options=config.toon_options
        )
    return _default_formatter


def set_default_formatter(formatter: ResponseFormatter) -> None:
    """
    Set the default response formatter instance.

    Args:
        formatter: ResponseFormatter instance to use as default
    """
    global _default_formatter
    _default_formatter = formatter


# Convenience functions using default formatter
def format_search_results(results: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
    """Format search results using default formatter."""
    return get_default_formatter().format_search_results(results)


def format_asset_list(assets: List[Dict[str, Any]]) -> Union[str, List[Dict[str, Any]]]:
    """Format asset list using default formatter."""
    return get_default_formatter().format_asset_list(assets)


def format_lineage_results(lineage_data: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
    """Format lineage results using default formatter."""
    return get_default_formatter().format_lineage_results(lineage_data)


def format_dsl_results(dsl_results: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
    """Format DSL results using default formatter."""
    return get_default_formatter().format_dsl_results(dsl_results)


def format_update_results(update_results: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
    """Format update results using default formatter."""
    return get_default_formatter().format_update_results(update_results)


def parse_parameter(param: Any) -> Any:
    """Parse parameter using TOON parameter parser."""
    return TOONParameterParser.parse_parameter(param)

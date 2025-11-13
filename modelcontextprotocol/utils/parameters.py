"""
Parameter parsing and validation utilities for MCP tools.

This module provides reusable functions for parsing and validating
parameters that are commonly used across different MCP tools.
"""

import json
import logging
from typing import Any, List, Optional, Union
from .formatting import parse_parameter

logger = logging.getLogger(__name__)


def parse_json_parameter(param: Any) -> Union[dict, list, None]:
    """
    Parse a parameter that might be a JSON or TOON string.

    This function now supports both JSON and TOON formats for maximum compatibility.
    It will first try to parse as TOON, then fall back to JSON if that fails.

    Args:
        param: The parameter value to parse (could be TOON string, JSON string, dict, list, etc.)

    Returns:
        The parsed parameter value

    Raises:
        json.JSONDecodeError: If neither TOON nor JSON parsing succeeds
    """
    if param is None:
        return None

    if isinstance(param, str):
        try:
            # Try TOON parsing first for better token efficiency
            return parse_parameter(param)
        except Exception as e:
            logger.debug(f"TOON parsing failed, trying JSON: {e}")
            try:
                return json.loads(param)
            except json.JSONDecodeError as json_e:
                logger.error(
                    f"Invalid parameter format (neither TOON nor JSON): {param}"
                )
                raise json_e

    return param


def parse_list_parameter(param: Any) -> Optional[List[Any]]:
    """
    Parse a parameter that might be a JSON string representing a list.

    Args:
        param: The parameter value to parse

    Returns:
        The parsed list, None if param is None, or original value converted to list if needed

    Raises:
        json.JSONDecodeError: If the JSON string is invalid
    """
    if param is None:
        return None

    if isinstance(param, str):
        try:
            parsed = json.loads(param)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON parameter: {param}")
            raise e

        if isinstance(parsed, list):
            return parsed
        return [parsed]

    if isinstance(param, list):
        return param

    return [param]

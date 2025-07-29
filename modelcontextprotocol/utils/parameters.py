"""
Parameter parsing and validation utilities for MCP tools.

This module provides reusable functions for parsing and validating
parameters that are commonly used across different MCP tools.
"""

import json
import logging
from typing import Any, List, Optional, Union

logger = logging.getLogger(__name__)


def parse_json_parameter(param: Any) -> Union[dict, list, None]:
    """
    Parse a parameter that might be a JSON string.

    Args:
        param: The parameter value to parse (could be string, dict, list, etc.)

    Returns:
        The parsed parameter value

    Raises:
        json.JSONDecodeError: If the JSON string is invalid
    """
    if param is None:
        return None

    if isinstance(param, str):
        try:
            return json.loads(param)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON parameter: {param}")
            raise e

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

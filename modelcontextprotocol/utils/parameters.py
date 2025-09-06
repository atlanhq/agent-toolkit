"""
Parameter parsing and validation utilities for MCP tools.

This module provides reusable functions for parsing and validating
parameters that are commonly used across different MCP tools.
"""

import logging
from typing import Any, List, Optional, Union
import orjson

logger = logging.getLogger(__name__)


def parse_json_parameter(param: Any) -> Union[dict, list, None]:
    """
    Parse a parameter that might be a JSON string.

    Args:
        param: The parameter value to parse (could be string, dict, list, etc.)

    Returns:
        The parsed parameter value

    Raises:
        orjson.JSONDecodeError: If the JSON string is invalid
    """
    if param is None or not isinstance(param, str):
        return param

    try:
        return orjson.loads(param)
    except orjson.JSONDecodeError as e:
        logger.error(f"Invalid JSON parameter: {param}")
        raise e


def parse_list_parameter(param: Any) -> Optional[List[Any]]:
    """
    Parse a parameter that might be a JSON string representing a list.

    Args:
        param: The parameter value to parse

    Returns:
        The parsed list, None if param is None, or original value converted to list if needed

    Raises:
        orjson.JSONDecodeError: If the JSON string is invalid
    """
    if param is None:
        return None

    if isinstance(param, list):
        return param

    if isinstance(param, str):
        try:
            parsed = orjson.loads(param)
        except orjson.JSONDecodeError as e:
            logger.error(f"Invalid JSON parameter: {param}")
            raise e

        if isinstance(parsed, list):
            return parsed
        return [parsed]

    return [param]

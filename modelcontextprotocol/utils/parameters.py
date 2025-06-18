"""
Parameter parsing and validation utilities for MCP tools.

This module provides reusable functions for parsing and validating
parameters that are commonly used across different MCP tools.
"""

import json
import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


class ParameterParsingError(Exception):
    """Custom exception for parameter parsing errors."""

    def __init__(self, value: Any, error_details: str):
        self.value = value
        self.error_details = error_details
        super().__init__(f"Parameter parsing error: {error_details}")


def parse_json_parameter(param: Any) -> Any:
    """
    Parse a parameter that might be a JSON string.

    Args:
        param: The parameter value to parse (could be string, dict, list, etc.)

    Returns:
        The parsed parameter value

    Raises:
        ParameterParsingError: If parsing fails or None value is not allowed
    """
    if param is None:
        return None

    if isinstance(param, str):
        try:
            return json.loads(param)
        except json.JSONDecodeError as e:
            raise ParameterParsingError(param, f"Invalid JSON string: {str(e)}")

    return param


def parse_list_parameter(param: Any) -> Optional[List[Any]]:
    """
    Parse a parameter that might be a JSON string representing a list.

    Args:
        param: The parameter value to parse

    Returns:
        The parsed list, None if param is None, or original value converted to list if needed

    Raises:
        ParameterParsingError: If JSON parsing fails
    """
    if param is None:
        return None

    if isinstance(param, str):
        try:
            parsed = json.loads(param)
            if isinstance(parsed, list):
                return parsed
            return [parsed]  # Convert single item to list
        except json.JSONDecodeError as e:
            raise ParameterParsingError(param, f"Invalid JSON string: {str(e)}")

    if isinstance(param, list):
        return param

    return [param]

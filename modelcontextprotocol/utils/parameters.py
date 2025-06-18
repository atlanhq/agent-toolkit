"""
Parameter parsing and validation utilities for MCP tools.

This module provides reusable functions for parsing and validating
parameters that are commonly used across different MCP tools.
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ParameterParsingError(Exception):
    """Custom exception for parameter parsing errors."""

    def __init__(self, parameter_name: str, value: Any, error_details: str):
        self.parameter_name = parameter_name
        self.value = value
        self.error_details = error_details
        super().__init__(f"Error parsing parameter '{parameter_name}': {error_details}")


def parse_json_parameter(
    param: Any, parameter_name: str = "parameter", allow_none: bool = True
) -> Any:
    """
    Parse a parameter that might be a JSON string.

    Args:
        param: The parameter value to parse (could be string, dict, list, etc.)
        parameter_name: Name of the parameter for error reporting
        allow_none: Whether to allow None values

    Returns:
        The parsed parameter value or original if parsing fails

    """
    if param is None:
        return None if allow_none else param

    if isinstance(param, str):
        try:
            return json.loads(param)
        except json.JSONDecodeError:
            return param

    return param


def parse_list_parameter(param: Any) -> Any:
    """
    Parse a parameter that might be a JSON string representing a list.

    Args:
        param: The parameter value to parse

    Returns:
        The parsed list, or original value converted to list if needed
    """
    if param is None:
        return None

    if isinstance(param, str):
        try:
            parsed = json.loads(param)
            if isinstance(parsed, list):
                return parsed
            return [parsed]  # Convert single item to list
        except json.JSONDecodeError:
            return [param]  # Convert string to single-item list

    if isinstance(param, list):
        return param

    # Convert single value to list
    return [param]

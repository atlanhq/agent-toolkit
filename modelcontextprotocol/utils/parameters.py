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
        The parsed parameter value

    Raises:
        ParameterParsingError: If JSON parsing fails and the value is not a simple type
    """
    if param is None:
        if allow_none:
            return None
        else:
            raise ParameterParsingError(parameter_name, param, "None value not allowed")

    if isinstance(param, str):
        # Try to parse as JSON first
        try:
            parsed_value = json.loads(param)
            logger.debug(f"Successfully parsed JSON for parameter '{parameter_name}'")
            return parsed_value
        except json.JSONDecodeError as e:
            logger.debug(
                f"Parameter '{parameter_name}' is not valid JSON, treating as string: {e}"
            )
            # If it's not valid JSON, return the original string
            return param

    # If it's already a dict, list, or other type, return as-is
    return param


def parse_list_parameter(
    param: Any,
    parameter_name: str = "parameter",
    allow_none: bool = True,
    ensure_list: bool = True,
) -> Optional[List[Any]]:
    """
    Parse a parameter that should be a list.

    Args:
        param: The parameter value to parse
        parameter_name: Name of the parameter for error reporting
        allow_none: Whether to allow None values
        ensure_list: Whether to convert single values to lists

    Returns:
        The parsed list or None if param is None and allow_none is True

    Raises:
        ParameterParsingError: If the parameter cannot be converted to a list
    """
    if param is None:
        if allow_none:
            return None
        else:
            raise ParameterParsingError(parameter_name, param, "None value not allowed")

    if isinstance(param, str):
        # Try to parse as JSON first
        try:
            parsed_value = json.loads(param)
            if isinstance(parsed_value, list):
                logger.debug(
                    f"Successfully parsed JSON list for parameter '{parameter_name}'"
                )
                return parsed_value
            elif ensure_list:
                logger.debug(
                    f"Converting parsed JSON value to list for parameter '{parameter_name}'"
                )
                return [parsed_value]
            else:
                raise ParameterParsingError(
                    parameter_name,
                    param,
                    f"Expected list but got {type(parsed_value).__name__}",
                )
        except json.JSONDecodeError:
            if ensure_list:
                logger.debug(
                    f"Converting string to single-item list for parameter '{parameter_name}'"
                )
                return [param]
            else:
                raise ParameterParsingError(
                    parameter_name, param, "String value cannot be converted to list"
                )

    if isinstance(param, list):
        return param

    if ensure_list:
        logger.debug(
            f"Converting single value to list for parameter '{parameter_name}'"
        )
        return [param]
    else:
        raise ParameterParsingError(
            parameter_name, param, f"Expected list but got {type(param).__name__}"
        )


def validate_integer_parameter(
    param: Any,
    parameter_name: str = "parameter",
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
    allow_none: bool = True,
) -> Optional[int]:
    """
    Validate and convert a parameter to integer.

    Args:
        param: The parameter value to validate
        parameter_name: Name of the parameter for error reporting
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        allow_none: Whether to allow None values

    Returns:
        The validated integer value or None if param is None and allow_none is True

    Raises:
        ParameterParsingError: If the parameter cannot be converted to integer or is out of range
    """
    if param is None:
        if allow_none:
            return None
        else:
            raise ParameterParsingError(parameter_name, param, "None value not allowed")

    try:
        int_value = int(param)
    except (ValueError, TypeError) as e:
        raise ParameterParsingError(
            parameter_name, param, f"Cannot convert to integer: {e}"
        )

    if min_value is not None and int_value < min_value:
        raise ParameterParsingError(
            parameter_name,
            param,
            f"Value {int_value} is less than minimum allowed value {min_value}",
        )

    if max_value is not None and int_value > max_value:
        raise ParameterParsingError(
            parameter_name,
            param,
            f"Value {int_value} is greater than maximum allowed value {max_value}",
        )

    return int_value


def validate_string_parameter(
    param: Any,
    parameter_name: str = "parameter",
    allowed_values: Optional[List[str]] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    allow_none: bool = True,
    allow_empty: bool = True,
) -> Optional[str]:
    """
    Validate and convert a parameter to string.

    Args:
        param: The parameter value to validate
        parameter_name: Name of the parameter for error reporting
        allowed_values: List of allowed string values
        min_length: Minimum allowed string length
        max_length: Maximum allowed string length
        allow_none: Whether to allow None values
        allow_empty: Whether to allow empty strings

    Returns:
        The validated string value or None if param is None and allow_none is True

    Raises:
        ParameterParsingError: If the parameter validation fails
    """
    if param is None:
        if allow_none:
            return None
        else:
            raise ParameterParsingError(parameter_name, param, "None value not allowed")

    str_value = str(param)

    if not allow_empty and not str_value:
        raise ParameterParsingError(parameter_name, param, "Empty string not allowed")

    if min_length is not None and len(str_value) < min_length:
        raise ParameterParsingError(
            parameter_name,
            param,
            f"String length {len(str_value)} is less than minimum {min_length}",
        )

    if max_length is not None and len(str_value) > max_length:
        raise ParameterParsingError(
            parameter_name,
            param,
            f"String length {len(str_value)} is greater than maximum {max_length}",
        )

    if allowed_values is not None and str_value not in allowed_values:
        raise ParameterParsingError(
            parameter_name,
            param,
            f"Value '{str_value}' not in allowed values: {allowed_values}",
        )

    return str_value


def parse_boolean_parameter(
    param: Any, parameter_name: str = "parameter", allow_none: bool = True
) -> Optional[bool]:
    """
    Parse and validate a boolean parameter.

    Args:
        param: The parameter value to parse
        parameter_name: Name of the parameter for error reporting
        allow_none: Whether to allow None values

    Returns:
        The parsed boolean value or None if param is None and allow_none is True

    Raises:
        ParameterParsingError: If the parameter cannot be converted to boolean
    """
    if param is None:
        if allow_none:
            return None
        else:
            raise ParameterParsingError(parameter_name, param, "None value not allowed")

    if isinstance(param, bool):
        return param

    if isinstance(param, str):
        lower_param = param.lower()
        if lower_param in ("true", "1", "yes", "on"):
            return True
        elif lower_param in ("false", "0", "no", "off"):
            return False
        else:
            raise ParameterParsingError(
                parameter_name, param, f"Cannot convert string '{param}' to boolean"
            )

    if isinstance(param, (int, float)):
        return bool(param)

    raise ParameterParsingError(
        parameter_name, param, f"Cannot convert {type(param).__name__} to boolean"
    )


# Legacy compatibility functions for existing code
def parse_json_param(param: Any) -> Any:
    """
    Legacy function for backward compatibility.

    Use parse_json_parameter() for new code.
    """
    return parse_json_parameter(param, "parameter", allow_none=True)


def parse_list_param(param: Any) -> Optional[List[Any]]:
    """
    Legacy function for backward compatibility.

    Use parse_list_parameter() for new code.
    """
    return parse_list_parameter(param, "parameter", allow_none=True, ensure_list=True)

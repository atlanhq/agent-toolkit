"""
TOON (Token-Oriented Object Notation) encoder/decoder for Python.

A compact data format optimized for transmitting structured information to Large Language Models (LLMs)
with 30-60% fewer tokens than JSON.

This implementation follows the TOON specification for maximum compatibility and token efficiency.
"""

import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class DelimiterType(str, Enum):
    """Supported delimiter types for TOON arrays."""

    COMMA = ","
    TAB = "\t"
    PIPE = "|"


@dataclass
class EncodeOptions:
    """Options for TOON encoding."""

    indent: int = 2
    delimiter: DelimiterType = DelimiterType.COMMA
    length_marker: Optional[str] = None  # "#" to enable length markers


@dataclass
class DecodeOptions:
    """Options for TOON decoding."""

    indent: int = 2
    strict: bool = True


class TOONEncoder:
    """TOON encoder for converting Python objects to TOON format."""

    def __init__(self, options: Optional[EncodeOptions] = None):
        """Initialize encoder with options."""
        self.options = options or EncodeOptions()
        self._current_indent = 0

    def encode(self, value: Any) -> str:
        """
        Encode a Python value to TOON format.

        Args:
            value: The value to encode (dict, list, or primitive)

        Returns:
            TOON-formatted string
        """
        self._current_indent = 0
        return self._encode_value(value).rstrip()

    def _encode_value(self, value: Any) -> str:
        """Encode any value to TOON format."""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            # Normalize numbers
            if isinstance(value, float):
                if value != value:  # NaN
                    return "null"
                elif value == float("inf") or value == float("-inf"):
                    return "null"
                elif value == -0.0:
                    return "0"
            return str(value)
        elif isinstance(value, str):
            return self._quote_string(value)
        elif isinstance(value, dict):
            return self._encode_object(value)
        elif isinstance(value, list):
            return self._encode_array(value)
        else:
            # Convert other types to string representation
            return self._quote_string(str(value))

    def _encode_object(self, obj: Dict[str, Any]) -> str:
        """Encode a dictionary as a TOON object."""
        if not obj:
            return "{}"

        lines = []
        for key, value in obj.items():
            encoded_value = self._encode_value(value)

            # Handle nested objects with proper indentation
            if isinstance(value, dict) and value:
                lines.append(f"{key}:")
                self._current_indent += self.options.indent
                nested_lines = encoded_value.split("\n")
                for line in nested_lines:
                    if line.strip():
                        lines.append(" " * self._current_indent + line)
                self._current_indent -= self.options.indent
            elif isinstance(value, list):
                # Arrays get special handling
                array_header, array_body = self._encode_array_with_header(key, value)
                lines.append(array_header)
                if array_body:
                    self._current_indent += self.options.indent
                    for line in array_body.split("\n"):
                        if line.strip():
                            lines.append(" " * self._current_indent + line)
                    self._current_indent -= self.options.indent
            else:
                lines.append(f"{key}: {encoded_value}")

        return "\n".join(lines)

    def _encode_array(self, arr: List[Any]) -> str:
        """Encode a list as a TOON array."""
        if not arr:
            return "[]"

        length = len(arr)
        length_marker = f"#{length}" if self.options.length_marker else str(length)

        # Check if this is a tabular array (uniform objects with primitive values)
        if self._is_tabular_array(arr):
            return self._encode_tabular_array(arr, length_marker)

        # Check if this is a primitive array
        if all(not isinstance(item, (dict, list)) for item in arr):
            return self._encode_primitive_array(arr, length_marker)

        # Mixed array - use list format
        return self._encode_mixed_array(arr, length_marker)

    def _encode_array_with_header(self, key: str, arr: List[Any]) -> tuple[str, str]:
        """Encode array with key as header."""
        if not arr:
            return f"{key}: []", ""

        length = len(arr)
        length_marker = f"#{length}" if self.options.length_marker else str(length)

        if self._is_tabular_array(arr):
            fields = list(arr[0].keys())
            delimiter_in_bracket = (
                self.options.delimiter.value
                if self.options.delimiter != DelimiterType.COMMA
                else ","
            )
            header = (
                f"{key}[{length_marker}{delimiter_in_bracket}]{{{','.join(fields)}}}:"
            )

            rows = []
            for item in arr:
                row_values = [self._format_cell_value(item[field]) for field in fields]
                rows.append(self.options.delimiter.value.join(row_values))

            return header, "\n".join(rows)

        elif all(not isinstance(item, (dict, list)) for item in arr):
            # Primitive array
            delimiter_suffix = (
                ""
                if self.options.delimiter == DelimiterType.COMMA
                else self.options.delimiter.value
            )
            header = f"{key}[{length_marker}{delimiter_suffix}]:"
            values = [self._format_cell_value(item) for item in arr]
            return header, self.options.delimiter.value.join(values)

        else:
            # Mixed array
            header = f"{key}[{length_marker}]:"
            lines = []
            for item in arr:
                if isinstance(item, dict):
                    if item:
                        lines.append(
                            "- " + self._encode_object(item).replace("\n", "\n  ")
                        )
                    else:
                        lines.append("- {}")
                else:
                    lines.append("- " + self._encode_value(item))
            return header, "\n".join(lines)

    def _is_tabular_array(self, arr: List[Any]) -> bool:
        """Check if array can be represented in tabular format."""
        if not arr or not isinstance(arr[0], dict):
            return False

        # All items must be dicts with same keys and primitive values
        first_keys = set(arr[0].keys())
        for item in arr:
            if not isinstance(item, dict):
                return False
            if set(item.keys()) != first_keys:
                return False
            # All values must be primitives
            for value in item.values():
                if isinstance(value, (dict, list)):
                    return False

        return True

    def _encode_tabular_array(
        self, arr: List[Dict[str, Any]], length_marker: str
    ) -> str:
        """Encode array as tabular format."""
        fields = list(arr[0].keys())
        delimiter_in_bracket = (
            self.options.delimiter.value
            if self.options.delimiter != DelimiterType.COMMA
            else ","
        )

        lines = [f"[{length_marker}{delimiter_in_bracket}]{{{','.join(fields)}}}:"]

        for item in arr:
            row_values = [self._format_cell_value(item[field]) for field in fields]
            lines.append("  " + self.options.delimiter.value.join(row_values))

        return "\n".join(lines)

    def _encode_primitive_array(self, arr: List[Any], length_marker: str) -> str:
        """Encode array of primitives."""
        delimiter_suffix = (
            ""
            if self.options.delimiter == DelimiterType.COMMA
            else self.options.delimiter.value
        )
        values = [self._format_cell_value(item) for item in arr]
        return f"[{length_marker}{delimiter_suffix}]: {self.options.delimiter.value.join(values)}"

    def _encode_mixed_array(self, arr: List[Any], length_marker: str) -> str:
        """Encode mixed array with list format."""
        lines = [f"[{length_marker}]:"]

        for item in arr:
            if isinstance(item, dict):
                if item:
                    encoded = self._encode_object(item)
                    # Indent the object content
                    indented_lines = []
                    for line in encoded.split("\n"):
                        indented_lines.append("    " + line)
                    lines.append("  -")
                    lines.extend(indented_lines)
                else:
                    lines.append("  - {}")
            else:
                lines.append("  - " + self._encode_value(item))

        return "\n".join(lines)

    def _format_cell_value(self, value: Any) -> str:
        """Format a value for use in array cells."""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            if isinstance(value, float):
                if value != value:  # NaN
                    return "null"
                elif value == float("inf") or value == float("-inf"):
                    return "null"
                elif value == -0.0:
                    return "0"
            return str(value)
        elif isinstance(value, str):
            return self._quote_string(value)
        else:
            return self._quote_string(str(value))

    def _quote_string(self, s: str) -> str:
        """Quote string if necessary according to TOON rules."""
        if not s:  # Empty string
            return '""'

        # Keywords that need quoting
        if s.lower() in ("null", "true", "false"):
            return f'"{s}"'

        # Numeric strings
        try:
            float(s)
            return f'"{s}"'
        except ValueError:
            pass

        # Leading/trailing whitespace
        if s != s.strip():
            return f'"{s}"'

        # Contains structural characters
        structural_chars = ':[]{}-"'
        if any(char in s for char in structural_chars):
            return f'"{s}"'

        # Contains current delimiter
        if self.options.delimiter.value in s:
            return f'"{s}"'

        # Contains control characters
        if any(ord(char) < 32 for char in s):
            return f'"{s}"'

        return s


class TOONDecoder:
    """TOON decoder for converting TOON format to Python objects."""

    def __init__(self, options: Optional[DecodeOptions] = None):
        """Initialize decoder with options."""
        self.options = options or DecodeOptions()

    def decode(self, toon_str: str) -> Any:
        """
        Decode a TOON-formatted string to Python objects.

        Args:
            toon_str: TOON-formatted string

        Returns:
            Decoded Python object
        """
        lines = toon_str.strip().split("\n")
        if not lines or not lines[0].strip():
            return None

        return self._parse_lines(lines, 0)[0]

    def _parse_lines(self, lines: List[str], start_idx: int) -> tuple[Any, int]:
        """Parse lines starting from start_idx, return (value, next_idx)."""
        if start_idx >= len(lines):
            return None, start_idx

        line = lines[start_idx].rstrip()

        # Skip empty lines
        if not line.strip():
            return self._parse_lines(lines, start_idx + 1)

        # Determine indentation level
        # indent_level = len(line) - len(line.lstrip())

        # Check for array format
        if "[" in line and "]:" in line:
            return self._parse_array(lines, start_idx)

        # Check for object key-value
        if ":" in line and not line.lstrip().startswith("-"):
            return self._parse_object(lines, start_idx)

        # Check for list item
        if line.lstrip().startswith("- "):
            # This should be handled by parent array parser
            return self._parse_primitive(line.lstrip()[2:]), start_idx + 1

        # Single primitive value
        return self._parse_primitive(line.strip()), start_idx + 1

    def _parse_object(
        self, lines: List[str], start_idx: int
    ) -> tuple[Dict[str, Any], int]:
        """Parse object from lines."""
        obj = {}
        current_idx = start_idx
        base_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())

        while current_idx < len(lines):
            line = lines[current_idx].rstrip()

            if not line.strip():
                current_idx += 1
                continue

            line_indent = len(line) - len(line.lstrip())

            # If we've moved to a different indentation level, we're done
            if line_indent < base_indent:
                break

            if line_indent > base_indent:
                # This should be handled by the parent key
                current_idx += 1
                continue

            # Parse key-value pair
            if ":" in line:
                key, _, value_part = line.partition(":")
                key = key.strip()
                value_part = value_part.strip()

                if value_part:
                    # Simple value on same line
                    obj[key] = self._parse_primitive(value_part)
                    current_idx += 1
                else:
                    # Complex value on following lines
                    value, next_idx = self._parse_lines(lines, current_idx + 1)
                    obj[key] = value
                    current_idx = next_idx
            else:
                current_idx += 1

        return obj, current_idx

    def _parse_array(self, lines: List[str], start_idx: int) -> tuple[Any, int]:
        """Parse array from lines."""
        line = lines[start_idx].strip()

        # Extract array header info
        bracket_start = line.find("[")
        bracket_end = line.find("]")

        if bracket_start == -1 or bracket_end == -1:
            raise ValueError(f"Invalid array format: {line}")

        header_part = line[bracket_end + 1 :].lstrip()
        if not header_part.startswith(":"):
            raise ValueError(f"Invalid array format: {line}")

        bracket_content = line[bracket_start + 1 : bracket_end]

        # Check for tabular format
        if "{" in header_part and "}" in header_part:
            return self._parse_tabular_array(lines, start_idx, bracket_content)

        # Check for primitive array (single line)
        value_part = header_part[1:].strip()
        if value_part and start_idx + 1 < len(lines):
            next_line = lines[start_idx + 1].strip()
            if not next_line.startswith("-") and next_line:
                # Single line primitive array
                return self._parse_primitive_array_line(
                    value_part, bracket_content
                ), start_idx + 2

        # Mixed array format
        return self._parse_mixed_array(lines, start_idx + 1, bracket_content)

    def _parse_tabular_array(
        self, lines: List[str], start_idx: int, bracket_content: str
    ) -> tuple[List[Dict[str, Any]], int]:
        """Parse tabular array format."""
        header_line = lines[start_idx]

        # Extract field names
        fields_start = header_line.find("{")
        fields_end = header_line.find("}")
        fields_str = header_line[fields_start + 1 : fields_end]
        fields = [f.strip() for f in fields_str.split(",")]

        # Determine delimiter
        delimiter = self._extract_delimiter(bracket_content)

        # Parse data rows
        results = []
        current_idx = start_idx + 1
        base_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())

        while current_idx < len(lines):
            line = lines[current_idx].rstrip()

            if not line.strip():
                current_idx += 1
                continue

            line_indent = len(line) - len(line.lstrip())

            # Check if we're still in the array
            if line_indent <= base_indent:
                break

            # Parse row
            row_data = line.strip()
            values = [v.strip() for v in row_data.split(delimiter)]

            if len(values) == len(fields):
                row_obj = {}
                for field, value in zip(fields, values):
                    row_obj[field] = self._parse_primitive(value)
                results.append(row_obj)

            current_idx += 1

        return results, current_idx

    def _parse_primitive_array_line(
        self, value_part: str, bracket_content: str
    ) -> List[Any]:
        """Parse primitive array from single line."""
        delimiter = self._extract_delimiter(bracket_content)
        values = [v.strip() for v in value_part.split(delimiter)]
        return [self._parse_primitive(v) for v in values]

    def _parse_mixed_array(
        self, lines: List[str], start_idx: int, bracket_content: str
    ) -> tuple[List[Any], int]:
        """Parse mixed array format."""
        results = []
        current_idx = start_idx
        base_indent = (
            len(lines[start_idx - 1]) - len(lines[start_idx - 1].lstrip())
            if start_idx > 0
            else 0
        )

        while current_idx < len(lines):
            line = lines[current_idx].rstrip()

            if not line.strip():
                current_idx += 1
                continue

            line_indent = len(line) - len(line.lstrip())

            if line_indent <= base_indent:
                break

            if line.lstrip().startswith("- "):
                # List item
                item_content = line.lstrip()[2:].strip()
                if item_content:
                    results.append(self._parse_primitive(item_content))
                else:
                    # Multi-line object
                    obj, next_idx = self._parse_object(lines, current_idx + 1)
                    results.append(obj)
                    current_idx = next_idx
                    continue

            current_idx += 1

        return results, current_idx

    def _extract_delimiter(self, bracket_content: str) -> str:
        """Extract delimiter from bracket content."""
        # Remove length marker
        content = re.sub(r"^#?\d+", "", bracket_content)

        if content == "," or not content:
            return ","
        elif content == "\t":
            return "\t"
        elif content == "|":
            return "|"
        else:
            return ","

    def _parse_primitive(self, value_str: str) -> Any:
        """Parse primitive value from string."""
        value_str = value_str.strip()

        if not value_str:
            return ""

        # Handle quoted strings
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]  # Remove quotes

        # Handle null
        if value_str.lower() == "null":
            return None

        # Handle booleans
        if value_str.lower() == "true":
            return True
        elif value_str.lower() == "false":
            return False

        # Try to parse as number
        try:
            if "." in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass

        # Return as string
        return value_str


def encode(value: Any, options: Optional[EncodeOptions] = None) -> str:
    """
    Encode a Python value to TOON format.

    Args:
        value: The value to encode
        options: Encoding options

    Returns:
        TOON-formatted string
    """
    encoder = TOONEncoder(options)
    return encoder.encode(value)


def decode(toon_str: str, options: Optional[DecodeOptions] = None) -> Any:
    """
    Decode a TOON-formatted string to Python objects.

    Args:
        toon_str: TOON-formatted string
        options: Decoding options

    Returns:
        Decoded Python object
    """
    decoder = TOONDecoder(options)
    return decoder.decode(toon_str)


def calculate_token_savings(original_json: str, toon_str: str) -> Dict[str, Any]:
    """
    Calculate token savings between JSON and TOON formats.

    Args:
        original_json: Original JSON string
        toon_str: TOON-formatted string

    Returns:
        Dictionary with savings statistics
    """
    json_length = len(original_json)
    toon_length = len(toon_str)

    if json_length == 0:
        return {"error": "Empty JSON string"}

    savings_chars = json_length - toon_length
    savings_percent = (savings_chars / json_length) * 100

    return {
        "json_length": json_length,
        "toon_length": toon_length,
        "savings_chars": savings_chars,
        "savings_percent": round(savings_percent, 1),
        "compression_ratio": round(toon_length / json_length, 3),
    }

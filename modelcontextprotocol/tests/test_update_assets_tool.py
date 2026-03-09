"""Tests for update_assets_tool JSON string input handling.

Verifies that the update_assets_tool correctly parses parameters
that arrive as JSON strings (a common behavior from MCP clients)
rather than native dicts/lists.

Regression test for: AICHAT-595
"""

import json
from unittest.mock import patch, MagicMock

import pytest

import sys
import os

# Add the modelcontextprotocol directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.parameters import parse_json_parameter, parse_list_parameter


class TestParseJsonParameter:
    """Tests for parse_json_parameter utility."""

    def test_dict_passthrough(self):
        """Native dict should be returned as-is."""
        data = {"guid": "abc-123", "name": "Test"}
        assert parse_json_parameter(data) == data

    def test_list_passthrough(self):
        """Native list should be returned as-is."""
        data = [{"guid": "abc-123"}]
        assert parse_json_parameter(data) == data

    def test_string_dict_parsed(self):
        """JSON string encoding a dict should be parsed to dict."""
        data = {"guid": "abc-123", "name": "Test", "type_name": "Table"}
        json_str = json.dumps(data)
        assert parse_json_parameter(json_str) == data

    def test_string_list_parsed(self):
        """JSON string encoding a list should be parsed to list."""
        data = [{"guid": "abc-123"}, {"guid": "def-456"}]
        json_str = json.dumps(data)
        assert parse_json_parameter(json_str) == data

    def test_none_returns_none(self):
        assert parse_json_parameter(None) is None

    def test_invalid_json_string_raises(self):
        with pytest.raises(json.JSONDecodeError):
            parse_json_parameter("{invalid json")


class TestParseListParameter:
    """Tests for parse_list_parameter utility."""

    def test_list_passthrough(self):
        data = ["value1", "value2"]
        assert parse_list_parameter(data) == data

    def test_string_list_parsed(self):
        data = ["VERIFIED"]
        json_str = json.dumps(data)
        assert parse_list_parameter(json_str) == data

    def test_string_single_value_wrapped(self):
        """A JSON string encoding a single value should be wrapped in a list."""
        json_str = json.dumps("VERIFIED")
        assert parse_list_parameter(json_str) == ["VERIFIED"]

    def test_single_value_wrapped(self):
        """A non-list, non-string value should be wrapped in a list."""
        assert parse_list_parameter(42) == [42]

    def test_none_returns_none(self):
        assert parse_list_parameter(None) is None

    def test_string_dict_wrapped(self):
        """A JSON string encoding a dict should be wrapped in a list."""
        data = {"operation": "append", "term_guids": ["guid-1"]}
        json_str = json.dumps(data)
        result = parse_list_parameter(json_str)
        assert result == [data]


class TestUpdateAssetsToolStringInputs:
    """Integration tests: update_assets_tool accepts JSON string parameters.

    These tests verify the regression fix for AICHAT-595 where the tool
    would reject JSON string inputs with Pydantic validation errors.
    """

    @patch("server.update_assets")
    @patch("server.get_settings")
    def test_assets_as_json_string(self, mock_settings, mock_update_assets):
        """update_assets_tool should accept assets as a JSON string."""
        from server import update_assets_tool

        mock_update_assets.return_value = {"updated_count": 1, "errors": []}

        assets_dict = {
            "guid": "19cb18b6-43e7-4373-8863-e997c9276d9e",
            "name": "Test Asset",
            "type_name": "DataProduct",
            "qualified_name": "default/test/asset",
        }
        assets_str = json.dumps(assets_dict)

        result = update_assets_tool(
            assets=assets_str,
            attribute_name="user_description",
            attribute_values=["New description"],
        )

        assert result["updated_count"] == 1
        assert mock_update_assets.called

    @patch("server.update_assets")
    @patch("server.get_settings")
    def test_attribute_values_as_json_string(self, mock_settings, mock_update_assets):
        """update_assets_tool should accept attribute_values as a JSON string."""
        from server import update_assets_tool

        mock_update_assets.return_value = {"updated_count": 1, "errors": []}

        assets_dict = {
            "guid": "19cb18b6-43e7-4373-8863-e997c9276d9e",
            "name": "Test Asset",
            "type_name": "DataProduct",
            "qualified_name": "default/test/asset",
        }
        attribute_values_str = json.dumps(["Updated user description"])

        result = update_assets_tool(
            assets=assets_dict,
            attribute_name="user_description",
            attribute_values=attribute_values_str,
        )

        assert result["updated_count"] == 1
        assert mock_update_assets.called

    @patch("server.update_assets")
    @patch("server.get_settings")
    def test_both_params_as_json_strings(self, mock_settings, mock_update_assets):
        """Both assets and attribute_values can arrive as JSON strings."""
        from server import update_assets_tool

        mock_update_assets.return_value = {"updated_count": 1, "errors": []}

        assets_dict = {
            "guid": "19cb18b6-43e7-4373-8863-e997c9276d9e",
            "name": "Test Asset",
            "type_name": "DataProduct",
            "qualified_name": "default/test/asset",
        }
        assets_str = json.dumps(assets_dict)
        attribute_values_str = json.dumps(["New description"])

        result = update_assets_tool(
            assets=assets_str,
            attribute_name="user_description",
            attribute_values=attribute_values_str,
        )

        assert result["updated_count"] == 1
        assert mock_update_assets.called

    @patch("server.update_assets")
    @patch("server.get_settings")
    def test_assets_list_as_json_string(self, mock_settings, mock_update_assets):
        """update_assets_tool should accept a list of assets as JSON string."""
        from server import update_assets_tool

        mock_update_assets.return_value = {"updated_count": 2, "errors": []}

        assets_list = [
            {
                "guid": "guid-1",
                "name": "Asset 1",
                "type_name": "Table",
                "qualified_name": "default/test/asset1",
            },
            {
                "guid": "guid-2",
                "name": "Asset 2",
                "type_name": "Table",
                "qualified_name": "default/test/asset2",
            },
        ]
        assets_str = json.dumps(assets_list)

        result = update_assets_tool(
            assets=assets_str,
            attribute_name="user_description",
            attribute_values=["Desc 1", "Desc 2"],
        )

        assert result["updated_count"] == 2

    def test_invalid_json_assets_returns_error(self):
        """Invalid JSON string for assets should return a clear error."""
        from server import update_assets_tool

        result = update_assets_tool(
            assets="{not valid json",
            attribute_name="user_description",
            attribute_values=["desc"],
        )

        assert "error" in result
        assert result["updated_count"] == 0

    @patch("server.update_assets")
    @patch("server.get_settings")
    def test_native_dict_still_works(self, mock_settings, mock_update_assets):
        """Native dict/list inputs should continue to work."""
        from server import update_assets_tool

        mock_update_assets.return_value = {"updated_count": 1, "errors": []}

        result = update_assets_tool(
            assets={
                "guid": "guid-1",
                "name": "Asset",
                "type_name": "Table",
                "qualified_name": "default/test/asset",
            },
            attribute_name="user_description",
            attribute_values=["Description"],
        )

        assert result["updated_count"] == 1

    @patch("server.update_assets")
    @patch("server.get_settings")
    def test_readme_update_with_string_params(self, mock_settings, mock_update_assets):
        """Readme updates should work when parameters arrive as JSON strings."""
        from server import update_assets_tool

        mock_update_assets.return_value = {"updated_count": 1, "errors": []}

        assets_dict = {
            "guid": "19cb18b6-43e7-4373-8863-e997c9276d9e",
            "name": "Data Product",
            "type_name": "DataProduct",
            "qualified_name": "default/test/product",
        }

        result = update_assets_tool(
            assets=json.dumps(assets_dict),
            attribute_name="readme",
            attribute_values=json.dumps(["# My README\nContent here"]),
        )

        assert result["updated_count"] == 1

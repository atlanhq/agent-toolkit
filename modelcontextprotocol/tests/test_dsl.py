"""Unit tests for tools.dsl module."""

import json
import unittest
from unittest.mock import Mock, patch

from tools.dsl import get_assets_by_dsl


class TestGetAssetsByDsl(unittest.TestCase):
    """Test cases for the get_assets_by_dsl function."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.sample_dsl_dict = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"__state": "ACTIVE"}},
                        {"terms": {"__typeName.keyword": ["Table"]}},
                    ]
                }
            },
            "size": 10,
        }

        self.sample_dsl_string = json.dumps(self.sample_dsl_dict)

    @patch("tools.dsl.SearchUtils.process_results")
    @patch("tools.dsl.get_atlan_client")
    def test_dsl_query_with_dict_input(
        self, mock_get_client: Mock, mock_process_results: Mock
    ) -> None:
        """Test DSL query execution with dictionary input."""
        # Setup mocks
        mock_client = Mock()
        mock_search_response = Mock()
        mock_client.asset.search.return_value = mock_search_response
        mock_get_client.return_value = mock_client

        expected_result = {
            "results": [{"name": "test_table", "type": "Table"}],
            "aggregations": {},
            "error": None,
        }
        mock_process_results.return_value = expected_result

        # Execute
        result = get_assets_by_dsl(self.sample_dsl_dict)

        # Verify
        self.assertEqual(result, expected_result)
        mock_client.asset.search.assert_called_once()
        mock_process_results.assert_called_once_with(mock_search_response)

    @patch("tools.dsl.SearchUtils.process_results")
    @patch("tools.dsl.get_atlan_client")
    def test_dsl_query_with_string_input(
        self, mock_get_client: Mock, mock_process_results: Mock
    ) -> None:
        """Test DSL query execution with JSON string input."""
        # Setup mocks
        mock_client = Mock()
        mock_search_response = Mock()
        mock_client.asset.search.return_value = mock_search_response
        mock_get_client.return_value = mock_client

        expected_result = {
            "results": [{"name": "test_table", "type": "Table"}],
            "aggregations": {},
            "error": None,
        }
        mock_process_results.return_value = expected_result

        # Execute
        result = get_assets_by_dsl(self.sample_dsl_string)

        # Verify
        self.assertEqual(result, expected_result)
        mock_client.asset.search.assert_called_once()
        mock_process_results.assert_called_once_with(mock_search_response)

    def test_invalid_json_string_input(self) -> None:
        """Test handling of invalid JSON string input."""
        invalid_json = '{"query": {"bool": invalid json}'

        result = get_assets_by_dsl(invalid_json)

        self.assertEqual(result["results"], [])
        self.assertEqual(result["aggregations"], {})
        self.assertEqual(result["error"], "Invalid JSON in DSL query")

    @patch("tools.dsl.get_atlan_client")
    def test_client_exception_handling(self, mock_get_client: Mock) -> None:
        """Test handling of client exceptions during search."""
        # Setup mock client to raise exception
        mock_client = Mock()
        mock_client.asset.search.side_effect = Exception("Search API Error")
        mock_get_client.return_value = mock_client

        # Execute
        result = get_assets_by_dsl(self.sample_dsl_dict)

        # Verify
        self.assertEqual(result["results"], [])
        self.assertEqual(result["aggregations"], {})
        self.assertEqual(result["error"], "Search API Error")

    @patch("tools.dsl.SearchUtils.process_results")
    @patch("tools.dsl.get_atlan_client")
    def test_index_search_request_creation(
        self, mock_get_client: Mock, mock_process_results: Mock
    ) -> None:
        """Test that IndexSearchRequest is created with correct parameters."""
        # Setup mocks
        mock_client = Mock()
        mock_search_response = Mock()
        mock_client.asset.search.return_value = mock_search_response
        mock_get_client.return_value = mock_client
        mock_process_results.return_value = {
            "results": [],
            "aggregations": {},
            "error": None,
        }

        # Execute
        get_assets_by_dsl(self.sample_dsl_dict)

        # Verify that search was called (IndexSearchRequest creation is internal)
        mock_client.asset.search.assert_called_once()

        # Get the call arguments to verify IndexSearchRequest properties
        call_args = mock_client.asset.search.call_args[0][0]
        self.assertTrue(hasattr(call_args, "dsl"))
        self.assertTrue(hasattr(call_args, "suppress_logs"))
        self.assertTrue(hasattr(call_args, "show_search_score"))
        self.assertTrue(hasattr(call_args, "exclude_meanings"))
        self.assertTrue(hasattr(call_args, "exclude_atlan_tags"))

    @patch("tools.dsl.SearchUtils.process_results")
    @patch("tools.dsl.get_atlan_client")
    def test_complex_dsl_query(
        self, mock_get_client: Mock, mock_process_results: Mock
    ) -> None:
        """Test DSL query with complex structure including aggregations."""
        complex_dsl = {
            "query": {
                "function_score": {
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"__state": "ACTIVE"}},
                                {"terms": {"certificateStatus": ["VERIFIED"]}},
                            ],
                            "filter": [
                                {"range": {"createTime": {"gte": 1640995200000}}}
                            ],
                        }
                    },
                    "functions": [
                        {"filter": {"match": {"starredBy": "user"}}, "weight": 10}
                    ],
                }
            },
            "aggs": {"types": {"terms": {"field": "__typeName.keyword"}}},
            "size": 20,
        }

        # Setup mocks
        mock_client = Mock()
        mock_search_response = Mock()
        mock_client.asset.search.return_value = mock_search_response
        mock_get_client.return_value = mock_client

        expected_result = {
            "results": [{"name": "verified_table", "certificateStatus": "VERIFIED"}],
            "aggregations": {"types": {"buckets": [{"key": "Table", "doc_count": 5}]}},
            "error": None,
        }
        mock_process_results.return_value = expected_result

        # Execute
        result = get_assets_by_dsl(complex_dsl)

        # Verify
        self.assertEqual(result, expected_result)
        mock_client.asset.search.assert_called_once()

    def test_empty_dsl_query(self) -> None:
        """Test handling of empty DSL query."""
        result = get_assets_by_dsl({})

        # Should not fail, but may return empty results or error depending on Atlan's response
        self.assertIn("results", result)
        self.assertIn("aggregations", result)
        self.assertIn("error", result)

    @patch("tools.dsl.json.loads")
    def test_json_decode_error_handling(self, mock_json_loads: Mock) -> None:
        """Test specific JSON decode error handling."""
        mock_json_loads.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)

        result = get_assets_by_dsl("invalid json string")

        self.assertEqual(result["results"], [])
        self.assertEqual(result["aggregations"], {})
        self.assertEqual(result["error"], "Invalid JSON in DSL query")


if __name__ == "__main__":
    unittest.main()

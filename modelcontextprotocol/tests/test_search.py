"""Unit tests for tools.search module."""

import unittest
from unittest.mock import Mock, patch

from tools.search import search_assets


class TestSearchAssets(unittest.TestCase):
    """Test cases for the search_assets function."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.sample_conditions = {
            "name": "test_table",
            "certificate_status": "VERIFIED",
        }

        self.sample_negative_conditions = {"description": "has_any_value"}

        self.sample_some_conditions = {"owner_users": ["user1", "user2"]}

    @patch("tools.search.SearchUtils.process_results")
    @patch("tools.search.get_atlan_client")
    @patch("tools.search.FluentSearch")
    def test_basic_search_with_conditions(
        self,
        mock_fluent_search: Mock,
        mock_get_client: Mock,
        mock_process_results: Mock,
    ) -> None:
        """Test basic asset search with simple conditions."""
        # Setup mocks
        mock_search_instance = Mock()
        mock_search_instance.where.return_value = mock_search_instance
        mock_search_instance.to_request.return_value = Mock()
        mock_fluent_search.return_value = mock_search_instance

        mock_client = Mock()
        mock_search_response = Mock()
        mock_client.asset.search.return_value = mock_search_response
        mock_get_client.return_value = mock_client

        expected_result = {
            "results": [{"name": "test_table", "certificateStatus": "VERIFIED"}],
            "aggregations": {},
            "error": None,
        }
        mock_process_results.return_value = expected_result

        # Execute
        result = search_assets(conditions=self.sample_conditions, limit=5)

        # Verify
        self.assertEqual(result, expected_result)
        mock_fluent_search.assert_called_once()
        mock_client.asset.search.assert_called_once()
        mock_process_results.assert_called_once_with(mock_search_response)

    @patch("tools.search.SearchUtils.process_results")
    @patch("tools.search.get_atlan_client")
    @patch("tools.search.FluentSearch")
    @patch("tools.search.CompoundQuery")
    def test_search_with_asset_type_string(
        self,
        mock_compound_query: Mock,
        mock_fluent_search: Mock,
        mock_get_client: Mock,
        mock_process_results: Mock,
    ) -> None:
        """Test search with asset type specified as string."""
        # Setup mocks
        mock_search_instance = Mock()
        mock_search_instance.where.return_value = mock_search_instance
        mock_search_instance.to_request.return_value = Mock()
        mock_fluent_search.return_value = mock_search_instance

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
        result = search_assets(asset_type="Table")

        # Verify
        self.assertIsNotNone(result)
        mock_search_instance.where.assert_called()
        mock_process_results.assert_called_once()

    @patch("tools.search.SearchUtils.process_results")
    @patch("tools.search.get_atlan_client")
    @patch("tools.search.FluentSearch")
    @patch("tools.search.CompoundQuery")
    def test_search_with_asset_type_class(
        self,
        mock_compound_query: Mock,
        mock_fluent_search: Mock,
        mock_get_client: Mock,
        mock_process_results: Mock,
    ) -> None:
        """Test search with asset type specified as class."""
        # Setup mocks
        mock_search_instance = Mock()
        mock_search_instance.where.return_value = mock_search_instance
        mock_search_instance.to_request.return_value = Mock()
        mock_fluent_search.return_value = mock_search_instance

        mock_client = Mock()
        mock_search_response = Mock()
        mock_client.asset.search.return_value = mock_search_response
        mock_get_client.return_value = mock_client

        mock_process_results.return_value = {
            "results": [],
            "aggregations": {},
            "error": None,
        }

        # Mock asset class
        mock_asset_class = Mock()
        mock_asset_class.__name__ = "Table"

        # Execute
        result = search_assets(asset_type=mock_asset_class)

        # Verify
        self.assertIsNotNone(result)
        mock_compound_query.asset_type.assert_called_once_with(mock_asset_class)
        mock_process_results.assert_called_once()

    @patch("tools.search.SearchUtils.process_results")
    @patch("tools.search.get_atlan_client")
    @patch("tools.search.FluentSearch")
    @patch("tools.search.CompoundQuery")
    def test_search_include_archived_false(
        self,
        mock_compound_query: Mock,
        mock_fluent_search: Mock,
        mock_get_client: Mock,
        mock_process_results: Mock,
    ) -> None:
        """Test search with include_archived=False (default)."""
        # Setup mocks
        mock_search_instance = Mock()
        mock_search_instance.where.return_value = mock_search_instance
        mock_search_instance.to_request.return_value = Mock()
        mock_fluent_search.return_value = mock_search_instance

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
        result = search_assets(include_archived=False)

        # Verify that active_assets filter was applied
        self.assertIsNotNone(result)
        mock_compound_query.active_assets.assert_called_once()
        mock_process_results.assert_called_once()

    @patch("tools.search.SearchUtils.process_results")
    @patch("tools.search.get_atlan_client")
    @patch("tools.search.FluentSearch")
    def test_search_include_archived_true(
        self,
        mock_fluent_search: Mock,
        mock_get_client: Mock,
        mock_process_results: Mock,
    ) -> None:
        """Test search with include_archived=True."""
        # Setup mocks
        mock_search_instance = Mock()
        mock_search_instance.where.return_value = mock_search_instance
        mock_search_instance.to_request.return_value = Mock()
        mock_fluent_search.return_value = mock_search_instance

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
        result = search_assets(include_archived=True)

        # Verify
        self.assertIsNotNone(result)
        mock_process_results.assert_called_once()

    @patch("tools.search.SearchUtils.process_results")
    @patch("tools.search.get_atlan_client")
    @patch("tools.search.FluentSearch")
    @patch("tools.search.CompoundQuery")
    def test_search_with_connection_qualified_name(
        self,
        mock_compound_query: Mock,
        mock_fluent_search: Mock,
        mock_get_client: Mock,
        mock_process_results: Mock,
    ) -> None:
        """Test search with connection qualified name filter."""
        # Setup mocks
        mock_search_instance = Mock()
        mock_search_instance.where.return_value = mock_search_instance
        mock_search_instance.to_request.return_value = Mock()
        mock_fluent_search.return_value = mock_search_instance

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
        result = search_assets(connection_qualified_name="default/snowflake/DB")

        # Verify
        self.assertIsNotNone(result)
        mock_process_results.assert_called_once()

    @patch("tools.search.SearchUtils.process_results")
    @patch("tools.search.get_atlan_client")
    @patch("tools.search.FluentSearch")
    @patch("tools.search.CompoundQuery")
    def test_search_with_tags(
        self,
        mock_compound_query: Mock,
        mock_fluent_search: Mock,
        mock_get_client: Mock,
        mock_process_results: Mock,
    ) -> None:
        """Test search with tags filter."""
        # Setup mocks
        mock_search_instance = Mock()
        mock_search_instance.where.return_value = mock_search_instance
        mock_search_instance.to_request.return_value = Mock()
        mock_fluent_search.return_value = mock_search_instance

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
        result = search_assets(tags=["PRD", "SENSITIVE"], directly_tagged=True)

        # Verify
        self.assertIsNotNone(result)
        mock_compound_query.tagged.assert_called_once_with(
            with_one_of=["PRD", "SENSITIVE"], directly=True
        )
        mock_process_results.assert_called_once()

    @patch("tools.search.SearchUtils.process_results")
    @patch("tools.search.get_atlan_client")
    @patch("tools.search.FluentSearch")
    def test_search_with_domain_guids(
        self,
        mock_fluent_search: Mock,
        mock_get_client: Mock,
        mock_process_results: Mock,
    ) -> None:
        """Test search with domain GUIDs filter."""
        # Setup mocks
        mock_search_instance = Mock()
        mock_search_instance.where.return_value = mock_search_instance
        mock_search_instance.to_request.return_value = Mock()
        mock_fluent_search.return_value = mock_search_instance

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
        result = search_assets(domain_guids=["domain-guid-1", "domain-guid-2"])

        # Verify
        self.assertIsNotNone(result)
        mock_process_results.assert_called_once()

    @patch("tools.search.SearchUtils._process_condition")
    @patch("tools.search.SearchUtils._get_asset_attribute")
    @patch("tools.search.SearchUtils.process_results")
    @patch("tools.search.get_atlan_client")
    @patch("tools.search.FluentSearch")
    def test_search_with_negative_conditions(
        self,
        mock_fluent_search: Mock,
        mock_get_client: Mock,
        mock_process_results: Mock,
        mock_get_attr: Mock,
        mock_process_condition: Mock,
    ) -> None:
        """Test search with negative conditions."""
        # Setup mocks
        mock_search_instance = Mock()
        mock_search_instance.where.return_value = mock_search_instance
        mock_search_instance.to_request.return_value = Mock()
        mock_fluent_search.return_value = mock_search_instance

        mock_client = Mock()
        mock_search_response = Mock()
        mock_client.asset.search.return_value = mock_search_response
        mock_get_client.return_value = mock_client

        mock_process_results.return_value = {
            "results": [],
            "aggregations": {},
            "error": None,
        }
        mock_get_attr.return_value = Mock()
        mock_process_condition.return_value = mock_search_instance

        # Execute
        result = search_assets(negative_conditions=self.sample_negative_conditions)

        # Verify
        self.assertIsNotNone(result)
        mock_process_condition.assert_called()
        mock_process_results.assert_called_once()

    @patch("tools.search.SearchUtils._process_condition")
    @patch("tools.search.SearchUtils._get_asset_attribute")
    @patch("tools.search.SearchUtils.process_results")
    @patch("tools.search.get_atlan_client")
    @patch("tools.search.FluentSearch")
    def test_search_with_some_conditions(
        self,
        mock_fluent_search: Mock,
        mock_get_client: Mock,
        mock_process_results: Mock,
        mock_get_attr: Mock,
        mock_process_condition: Mock,
    ) -> None:
        """Test search with some conditions and min_somes."""
        # Setup mocks
        mock_search_instance = Mock()
        mock_search_instance.where.return_value = mock_search_instance
        mock_search_instance.min_somes.return_value = mock_search_instance
        mock_search_instance.to_request.return_value = Mock()
        mock_fluent_search.return_value = mock_search_instance

        mock_client = Mock()
        mock_search_response = Mock()
        mock_client.asset.search.return_value = mock_search_response
        mock_get_client.return_value = mock_client

        mock_process_results.return_value = {
            "results": [],
            "aggregations": {},
            "error": None,
        }
        mock_get_attr.return_value = Mock()
        mock_process_condition.return_value = mock_search_instance

        # Execute
        result = search_assets(some_conditions=self.sample_some_conditions, min_somes=2)

        # Verify
        self.assertIsNotNone(result)
        mock_process_condition.assert_called()
        mock_search_instance.min_somes.assert_called_once_with(2)
        mock_process_results.assert_called_once()

    def test_invalid_conditions_type(self) -> None:
        """Test error handling for invalid conditions type."""
        result = search_assets(conditions="invalid_string_condition")

        # Should return empty list for invalid conditions
        self.assertEqual(result, [])

    @patch("tools.search.get_atlan_client")
    def test_client_exception_handling(self, mock_get_client: Mock) -> None:
        """Test handling of client exceptions during search."""
        # Setup mock client to raise exception
        mock_client = Mock()
        mock_client.asset.search.side_effect = Exception("Search API Error")
        mock_get_client.return_value = mock_client

        # Execute
        result = search_assets(conditions={"name": "test"})

        # Verify - should return error response on exception
        self.assertEqual(
            result, [{"results": [], "aggregations": {}, "error": "Search API Error"}]
        )

    @patch("tools.search.SearchUtils.process_results")
    @patch("tools.search.get_atlan_client")
    @patch("tools.search.FluentSearch")
    def test_search_with_date_range(
        self,
        mock_fluent_search: Mock,
        mock_get_client: Mock,
        mock_process_results: Mock,
    ) -> None:
        """Test search with date range filters."""
        # Setup mocks
        mock_search_instance = Mock()
        mock_search_instance.where.return_value = mock_search_instance
        mock_search_instance.to_request.return_value = Mock()
        mock_fluent_search.return_value = mock_search_instance

        mock_client = Mock()
        mock_search_response = Mock()
        mock_client.asset.search.return_value = mock_search_response
        mock_get_client.return_value = mock_client

        mock_process_results.return_value = {
            "results": [],
            "aggregations": {},
            "error": None,
        }

        date_range = {"create_time": {"gte": 1640995200000, "lte": 1672531200000}}

        # Execute
        result = search_assets(date_range=date_range)

        # Verify
        self.assertIsNotNone(result)
        mock_process_results.assert_called_once()

    @patch("tools.search.SearchUtils.process_results")
    @patch("tools.search.get_atlan_client")
    @patch("tools.search.FluentSearch")
    def test_search_with_guids_filter(
        self,
        mock_fluent_search: Mock,
        mock_get_client: Mock,
        mock_process_results: Mock,
    ) -> None:
        """Test search with GUIDs filter."""
        # Setup mocks
        mock_search_instance = Mock()
        mock_search_instance.where.return_value = mock_search_instance
        mock_search_instance.to_request.return_value = Mock()
        mock_fluent_search.return_value = mock_search_instance

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
        result = search_assets(guids=["guid-1", "guid-2", "guid-3"])

        # Verify
        self.assertIsNotNone(result)
        mock_process_results.assert_called_once()

    @patch("tools.search.SearchUtils.process_results")
    @patch("tools.search.get_atlan_client")
    @patch("tools.search.FluentSearch")
    def test_search_with_pagination(
        self,
        mock_fluent_search: Mock,
        mock_get_client: Mock,
        mock_process_results: Mock,
    ) -> None:
        """Test search with pagination parameters."""
        # Setup mocks
        mock_search_instance = Mock()
        mock_search_instance.where.return_value = mock_search_instance
        mock_search_instance.page_size.return_value = mock_search_instance
        mock_search_instance.from_offset.return_value = mock_search_instance
        mock_search_instance.include_on_results.return_value = mock_search_instance
        mock_search_instance.include_on_relations.return_value = mock_search_instance
        mock_search_instance.to_request.return_value = Mock()
        mock_fluent_search.return_value = mock_search_instance

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
        result = search_assets(limit=50, offset=100)

        # Verify
        self.assertIsNotNone(result)
        mock_search_instance.page_size.assert_called_once_with(50)
        mock_search_instance.from_offset.assert_called_once_with(100)
        mock_process_results.assert_called_once()

    @patch("tools.search.SearchUtils.process_results")
    @patch("tools.search.get_atlan_client")
    @patch("tools.search.FluentSearch")
    def test_search_with_sorting(
        self,
        mock_fluent_search: Mock,
        mock_get_client: Mock,
        mock_process_results: Mock,
    ) -> None:
        """Test search with sorting parameters."""
        # Setup mocks
        mock_search_instance = Mock()
        mock_search_instance.where.return_value = mock_search_instance
        mock_search_instance.sort.return_value = mock_search_instance
        mock_search_instance.to_request.return_value = Mock()
        mock_fluent_search.return_value = mock_search_instance

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
        result = search_assets(sort_by="name", sort_order="DESC")

        # Verify
        self.assertIsNotNone(result)
        mock_process_results.assert_called_once()


if __name__ == "__main__":
    unittest.main()

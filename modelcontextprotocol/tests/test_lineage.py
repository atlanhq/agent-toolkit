"""Unit tests for tools.lineage module."""

import unittest
from unittest.mock import Mock, patch

from pyatlan.model.enums import LineageDirection
from tools.lineage import traverse_lineage


class TestTraverseLineage(unittest.TestCase):
    """Test cases for the traverse_lineage function."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_guid = "test-asset-guid-123"
        self.sample_lineage_assets = [
            Mock(guid="upstream-asset-1", name="Upstream Table 1"),
            Mock(guid="upstream-asset-2", name="Upstream Table 2"),
            Mock(guid="current-asset", name="Current Table"),
        ]

    @patch("tools.lineage.get_atlan_client")
    @patch("tools.lineage.FluentLineage")
    def test_traverse_upstream_lineage(
        self, mock_fluent_lineage: Mock, mock_get_client: Mock
    ) -> None:
        """Test traversing upstream lineage."""
        # Setup mocks
        mock_request = Mock()
        mock_lineage_instance = Mock()
        mock_lineage_instance.direction.return_value = mock_lineage_instance
        mock_lineage_instance.depth.return_value = mock_lineage_instance
        mock_lineage_instance.size.return_value = mock_lineage_instance
        mock_lineage_instance.immediate_neighbors.return_value = mock_lineage_instance
        mock_lineage_instance.request = mock_request
        mock_fluent_lineage.return_value = mock_lineage_instance

        mock_client = Mock()
        mock_client.asset.get_lineage_list.return_value = self.sample_lineage_assets
        mock_get_client.return_value = mock_client

        # Execute
        result = traverse_lineage(
            guid=self.test_guid,
            direction=LineageDirection.UPSTREAM,
            depth=5,
            size=20,
            immediate_neighbors=True,
        )

        # Verify
        self.assertEqual(len(result["assets"]), 3)
        self.assertNotIn("error", result)

        # Verify FluentLineage was configured correctly
        mock_fluent_lineage.assert_called_once_with(starting_guid=self.test_guid)
        mock_lineage_instance.direction.assert_called_once_with(
            LineageDirection.UPSTREAM
        )
        mock_lineage_instance.depth.assert_called_once_with(5)
        mock_lineage_instance.size.assert_called_once_with(20)
        mock_lineage_instance.immediate_neighbors.assert_called_once_with(True)

        # Verify client call
        mock_client.asset.get_lineage_list.assert_called_once_with(mock_request)

    @patch("tools.lineage.get_atlan_client")
    @patch("tools.lineage.FluentLineage")
    def test_traverse_downstream_lineage(
        self, mock_fluent_lineage: Mock, mock_get_client: Mock
    ) -> None:
        """Test traversing downstream lineage."""
        # Setup mocks
        mock_request = Mock()
        mock_lineage_instance = Mock()
        mock_lineage_instance.direction.return_value = mock_lineage_instance
        mock_lineage_instance.depth.return_value = mock_lineage_instance
        mock_lineage_instance.size.return_value = mock_lineage_instance
        mock_lineage_instance.immediate_neighbors.return_value = mock_lineage_instance
        mock_lineage_instance.request = mock_request
        mock_fluent_lineage.return_value = mock_lineage_instance

        mock_client = Mock()
        downstream_assets = [Mock(guid="downstream-asset-1", name="Downstream View")]
        mock_client.asset.get_lineage_list.return_value = downstream_assets
        mock_get_client.return_value = mock_client

        # Execute
        result = traverse_lineage(
            guid=self.test_guid, direction=LineageDirection.DOWNSTREAM
        )

        # Verify
        self.assertEqual(len(result["assets"]), 1)
        self.assertNotIn("error", result)
        mock_lineage_instance.direction.assert_called_once_with(
            LineageDirection.DOWNSTREAM
        )

    @patch("tools.lineage.get_atlan_client")
    @patch("tools.lineage.FluentLineage")
    def test_default_parameters(
        self, mock_fluent_lineage: Mock, mock_get_client: Mock
    ) -> None:
        """Test traverse_lineage with default parameters."""
        # Setup mocks
        mock_request = Mock()
        mock_lineage_instance = Mock()
        mock_lineage_instance.direction.return_value = mock_lineage_instance
        mock_lineage_instance.depth.return_value = mock_lineage_instance
        mock_lineage_instance.size.return_value = mock_lineage_instance
        mock_lineage_instance.immediate_neighbors.return_value = mock_lineage_instance
        mock_lineage_instance.request = mock_request
        mock_fluent_lineage.return_value = mock_lineage_instance

        mock_client = Mock()
        mock_client.asset.get_lineage_list.return_value = []
        mock_get_client.return_value = mock_client

        # Execute with minimal parameters
        result = traverse_lineage(
            guid=self.test_guid, direction=LineageDirection.UPSTREAM
        )

        # Verify default values were used
        mock_lineage_instance.depth.assert_called_once_with(1000000)
        mock_lineage_instance.size.assert_called_once_with(10)
        mock_lineage_instance.immediate_neighbors.assert_called_once_with(False)
        self.assertEqual(result["assets"], [])

    @patch("tools.lineage.get_atlan_client")
    @patch("tools.lineage.FluentLineage")
    def test_none_response_handling(
        self, mock_fluent_lineage: Mock, mock_get_client: Mock
    ) -> None:
        """Test handling of None response from lineage API."""
        # Setup mocks
        mock_request = Mock()
        mock_lineage_instance = Mock()
        mock_lineage_instance.direction.return_value = mock_lineage_instance
        mock_lineage_instance.depth.return_value = mock_lineage_instance
        mock_lineage_instance.size.return_value = mock_lineage_instance
        mock_lineage_instance.immediate_neighbors.return_value = mock_lineage_instance
        mock_lineage_instance.request = mock_request
        mock_fluent_lineage.return_value = mock_lineage_instance

        mock_client = Mock()
        mock_client.asset.get_lineage_list.return_value = None
        mock_get_client.return_value = mock_client

        # Execute
        result = traverse_lineage(
            guid=self.test_guid, direction=LineageDirection.UPSTREAM
        )

        # Verify
        self.assertEqual(result["assets"], [])
        self.assertNotIn("error", result)

    @patch("tools.lineage.get_atlan_client")
    @patch("tools.lineage.FluentLineage")
    def test_response_with_none_items(
        self, mock_fluent_lineage: Mock, mock_get_client: Mock
    ) -> None:
        """Test handling of response containing None items."""
        # Setup mocks
        mock_request = Mock()
        mock_lineage_instance = Mock()
        mock_lineage_instance.direction.return_value = mock_lineage_instance
        mock_lineage_instance.depth.return_value = mock_lineage_instance
        mock_lineage_instance.size.return_value = mock_lineage_instance
        mock_lineage_instance.immediate_neighbors.return_value = mock_lineage_instance
        mock_lineage_instance.request = mock_request
        mock_fluent_lineage.return_value = mock_lineage_instance

        mock_client = Mock()
        # Response with some None items mixed in
        response_with_nones = [
            Mock(guid="asset-1", name="Asset 1"),
            None,
            Mock(guid="asset-2", name="Asset 2"),
            None,
        ]
        mock_client.asset.get_lineage_list.return_value = response_with_nones
        mock_get_client.return_value = mock_client

        # Execute
        result = traverse_lineage(
            guid=self.test_guid, direction=LineageDirection.UPSTREAM
        )

        # Verify - should filter out None items
        self.assertEqual(len(result["assets"]), 2)
        self.assertNotIn("error", result)

    @patch("tools.lineage.get_atlan_client")
    @patch("tools.lineage.FluentLineage")
    def test_client_exception_handling(
        self, mock_fluent_lineage: Mock, mock_get_client: Mock
    ) -> None:
        """Test handling of client exceptions during lineage traversal."""
        # Setup mocks
        mock_request = Mock()
        mock_lineage_instance = Mock()
        mock_lineage_instance.direction.return_value = mock_lineage_instance
        mock_lineage_instance.depth.return_value = mock_lineage_instance
        mock_lineage_instance.size.return_value = mock_lineage_instance
        mock_lineage_instance.immediate_neighbors.return_value = mock_lineage_instance
        mock_lineage_instance.request = mock_request
        mock_fluent_lineage.return_value = mock_lineage_instance

        mock_client = Mock()
        mock_client.asset.get_lineage_list.side_effect = Exception("Lineage API Error")
        mock_get_client.return_value = mock_client

        # Execute
        result = traverse_lineage(
            guid=self.test_guid, direction=LineageDirection.UPSTREAM
        )

        # Verify
        self.assertEqual(result["assets"], [])
        self.assertEqual(result["error"], "Lineage API Error")

    @patch("tools.lineage.get_atlan_client")
    @patch("tools.lineage.FluentLineage")
    def test_fluent_lineage_exception_handling(
        self, mock_fluent_lineage: Mock, mock_get_client: Mock
    ) -> None:
        """Test handling of FluentLineage construction exceptions."""
        # Setup mock to raise exception during FluentLineage creation
        mock_fluent_lineage.side_effect = Exception("FluentLineage construction error")

        # Execute
        result = traverse_lineage(
            guid=self.test_guid, direction=LineageDirection.UPSTREAM
        )

        # Verify
        self.assertEqual(result["assets"], [])
        self.assertEqual(result["error"], "FluentLineage construction error")

    @patch("tools.lineage.get_atlan_client")
    @patch("tools.lineage.FluentLineage")
    def test_large_depth_and_size_parameters(
        self, mock_fluent_lineage: Mock, mock_get_client: Mock
    ) -> None:
        """Test traverse_lineage with large depth and size parameters."""
        # Setup mocks
        mock_request = Mock()
        mock_lineage_instance = Mock()
        mock_lineage_instance.direction.return_value = mock_lineage_instance
        mock_lineage_instance.depth.return_value = mock_lineage_instance
        mock_lineage_instance.size.return_value = mock_lineage_instance
        mock_lineage_instance.immediate_neighbors.return_value = mock_lineage_instance
        mock_lineage_instance.request = mock_request
        mock_fluent_lineage.return_value = mock_lineage_instance

        mock_client = Mock()
        mock_client.asset.get_lineage_list.return_value = []
        mock_get_client.return_value = mock_client

        # Execute with large parameters
        result = traverse_lineage(
            guid=self.test_guid,
            direction=LineageDirection.DOWNSTREAM,
            depth=999999,
            size=1000,
            immediate_neighbors=False,
        )

        # Verify parameters were passed correctly
        mock_lineage_instance.depth.assert_called_once_with(999999)
        mock_lineage_instance.size.assert_called_once_with(1000)
        mock_lineage_instance.immediate_neighbors.assert_called_once_with(False)
        self.assertEqual(result["assets"], [])


if __name__ == "__main__":
    unittest.main()

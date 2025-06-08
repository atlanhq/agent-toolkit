"""Unit tests for tools.assets module."""

import unittest
from unittest.mock import Mock, patch

from tools.assets import update_assets
from tools.models import UpdatableAsset, UpdatableAttribute, CertificateStatus


class TestUpdateAssets(unittest.TestCase):
    """Test cases for the update_assets function."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.sample_asset = UpdatableAsset(
            guid="test-guid-1",
            name="Test Asset",
            qualified_name="default/test/asset",
            type_name="Table",
        )

        self.sample_assets = [
            UpdatableAsset(
                guid="test-guid-1",
                name="Test Asset 1",
                qualified_name="default/test/asset1",
                type_name="Table",
            ),
            UpdatableAsset(
                guid="test-guid-2",
                name="Test Asset 2",
                qualified_name="default/test/asset2",
                type_name="Column",
            ),
        ]

    @patch("tools.assets.get_atlan_client")
    def test_update_single_asset_user_description(self, mock_get_client: Mock) -> None:
        """Test updating user description for a single asset."""
        # Setup mock client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.guid_assignments = ["test-guid-1"]
        mock_client.asset.save.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Execute
        result = update_assets(
            updatable_assets=self.sample_asset,
            attribute_name=UpdatableAttribute.USER_DESCRIPTION,
            attribute_values=["Updated description"],
        )

        # Verify
        self.assertEqual(result["updated_count"], 1)
        self.assertEqual(result["errors"], [])
        mock_client.asset.save.assert_called_once()

    @patch("tools.assets.get_atlan_client")
    def test_update_multiple_assets_certificate_status(
        self, mock_get_client: Mock
    ) -> None:
        """Test updating certificate status for multiple assets."""
        # Setup mock client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.guid_assignments = ["test-guid-1", "test-guid-2"]
        mock_client.asset.save.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Execute
        result = update_assets(
            updatable_assets=self.sample_assets,
            attribute_name=UpdatableAttribute.CERTIFICATE_STATUS,
            attribute_values=[CertificateStatus.VERIFIED, CertificateStatus.DRAFT],
        )

        # Verify
        self.assertEqual(result["updated_count"], 2)
        self.assertEqual(result["errors"], [])
        mock_client.asset.save.assert_called_once()

    def test_mismatched_assets_and_values_count(self) -> None:
        """Test error when number of assets doesn't match number of values."""
        result = update_assets(
            updatable_assets=self.sample_assets,
            attribute_name=UpdatableAttribute.USER_DESCRIPTION,
            attribute_values=["Only one description"],  # Should be 2 values
        )

        self.assertEqual(result["updated_count"], 0)
        self.assertIn(
            "Number of asset GUIDs must match number of attribute values",
            result["errors"][0],
        )

    @patch("tools.assets.get_atlan_client")
    def test_invalid_certificate_status(self, mock_get_client: Mock) -> None:
        """Test error with invalid certificate status value."""
        # Setup mock client (even though we won't reach it due to validation error)
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        result = update_assets(
            updatable_assets=self.sample_asset,
            attribute_name=UpdatableAttribute.CERTIFICATE_STATUS,
            attribute_values=["INVALID_STATUS"],
        )

        self.assertEqual(result["updated_count"], 0)
        # The error message could be either our custom validation or Pydantic's validation
        self.assertTrue(
            "Invalid certificate status: INVALID_STATUS" in result["errors"][0]
            or "value is not a valid enumeration member" in result["errors"][0]
        )

    @patch("tools.assets.get_atlan_client")
    def test_client_exception_handling(self, mock_get_client: Mock) -> None:
        """Test handling of client exceptions."""
        # Setup mock client to raise exception
        mock_client = Mock()
        mock_client.asset.save.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client

        # Execute
        result = update_assets(
            updatable_assets=self.sample_asset,
            attribute_name=UpdatableAttribute.USER_DESCRIPTION,
            attribute_values=["Test description"],
        )

        # Verify
        self.assertEqual(result["updated_count"], 0)
        self.assertIn("Error updating assets: API Error", result["errors"][0])

    @patch("tools.assets.get_atlan_client")
    def test_convert_single_asset_to_list(self, mock_get_client: Mock) -> None:
        """Test that single asset is properly converted to list."""
        # Setup mock client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.guid_assignments = ["test-guid-1"]
        mock_client.asset.save.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Execute with single asset (not in list)
        result = update_assets(
            updatable_assets=self.sample_asset,
            attribute_name=UpdatableAttribute.USER_DESCRIPTION,
            attribute_values=["Test description"],
        )

        # Verify
        self.assertEqual(result["updated_count"], 1)
        self.assertEqual(result["errors"], [])

    @patch("tools.assets.get_atlan_client")
    def test_asset_class_import_and_updater(self, mock_get_client: Mock) -> None:
        """Test that asset class is properly imported and updater is called."""
        # Setup mock client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.guid_assignments = ["test-guid-1"]
        mock_client.asset.save.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Execute - this will test the actual import and getattr functionality
        result = update_assets(
            updatable_assets=self.sample_asset,
            attribute_name=UpdatableAttribute.USER_DESCRIPTION,
            attribute_values=["Test description"],
        )

        # Verify that the function completed successfully
        self.assertEqual(result["updated_count"], 1)
        self.assertEqual(result["errors"], [])
        mock_client.asset.save.assert_called_once()


if __name__ == "__main__":
    unittest.main()

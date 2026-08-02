import unittest
from unittest.mock import MagicMock, patch

from tools.models import (
    UpdatableAttribute,
    UpdatableAsset,
    TagOperation,
    TagOperations,
)
from tools.assets import update_assets
from server import update_assets_tool


class TestTagModels(unittest.TestCase):
    """Unit tests for tag-related data models."""

    def test_tag_operation_enum(self):
        self.assertEqual(TagOperation.ADD.value, "add")
        self.assertEqual(TagOperation.REPLACE.value, "replace")
        self.assertEqual(TagOperation.REMOVE.value, "remove")

    def test_updatable_attribute_tag(self):
        self.assertEqual(UpdatableAttribute.TAG.value, "tag")
        self.assertIn("tag", [attr.value for attr in UpdatableAttribute])

    def test_tag_operations_model_defaults(self):
        op = TagOperations(operation=TagOperation.ADD, tag_names=["PII", "Confidential"])
        self.assertEqual(op.operation, TagOperation.ADD)
        self.assertEqual(op.tag_names, ["PII", "Confidential"])
        self.assertFalse(op.propagate)
        self.assertTrue(op.remove_propagation_on_delete)
        self.assertFalse(op.restrict_lineage_propagation)
        self.assertFalse(op.restrict_propagation_through_hierarchy)

    def test_tag_operations_model_custom_values(self):
        op = TagOperations(
            operation="replace",
            tag_names=["Public"],
            propagate=True,
            remove_propagation_on_delete=False,
            restrict_lineage_propagation=True,
            restrict_propagation_through_hierarchy=True,
        )
        self.assertEqual(op.operation, TagOperation.REPLACE)
        self.assertEqual(op.tag_names, ["Public"])
        self.assertTrue(op.propagate)
        self.assertFalse(op.remove_propagation_on_delete)
        self.assertTrue(op.restrict_lineage_propagation)
        self.assertTrue(op.restrict_propagation_through_hierarchy)


class TestUpdateAssetsWithTags(unittest.TestCase):
    """Unit tests for update_assets tool with UpdatableAttribute.TAG."""

    def setUp(self):
        self.mock_client = MagicMock()
        # Mock tag cache to recognize 'PII', 'Confidential', and 'Public'
        self.mock_client.atlan_tag_cache.get_id_for_name.side_effect = (
            lambda name: "tag-id-" + name.lower() if name in ["PII", "Confidential", "Public"] else None
        )

        self.asset1 = UpdatableAsset(
            guid="guid-123",
            name="CustomerTable",
            type_name="Table",
            qualified_name="default/snowflake/123/CUSTOMER_TABLE",
        )
        self.asset2 = UpdatableAsset(
            guid="guid-456",
            name="OrdersTable",
            type_name="Table",
            qualified_name="default/snowflake/123/ORDERS_TABLE",
        )

    @patch("tools.assets.get_atlan_client")
    def test_add_tags_success(self, mock_get_client):
        mock_get_client.return_value = self.mock_client

        tag_op = TagOperations(
            operation=TagOperation.ADD,
            tag_names=["PII", "Confidential"],
            propagate=True,
        )

        result = update_assets(
            updatable_assets=[self.asset1],
            attribute_name=UpdatableAttribute.TAG,
            attribute_values=[tag_op],
        )

        self.assertEqual(result["updated_count"], 1)
        self.assertEqual(len(result["errors"]), 0)
        self.mock_client.asset.add_atlan_tags.assert_called_once()
        call_kwargs = self.mock_client.asset.add_atlan_tags.call_args[1]
        self.assertEqual(call_kwargs["qualified_name"], self.asset1.qualified_name)
        self.assertEqual(call_kwargs["atlan_tag_names"], ["PII", "Confidential"])
        self.assertTrue(call_kwargs["propagate"])

    @patch("tools.assets.get_atlan_client")
    def test_remove_tags_success(self, mock_get_client):
        mock_get_client.return_value = self.mock_client

        tag_op = TagOperations(
            operation=TagOperation.REMOVE,
            tag_names=["PII"],
        )

        result = update_assets(
            updatable_assets=[self.asset1],
            attribute_name=UpdatableAttribute.TAG,
            attribute_values=[tag_op],
        )

        self.assertEqual(result["updated_count"], 1)
        self.assertEqual(len(result["errors"]), 0)
        self.mock_client.asset.remove_atlan_tags.assert_called_once()
        call_kwargs = self.mock_client.asset.remove_atlan_tags.call_args[1]
        self.assertEqual(call_kwargs["qualified_name"], self.asset1.qualified_name)
        self.assertEqual(call_kwargs["atlan_tag_names"], ["PII"])

    @patch("tools.assets.get_atlan_client")
    def test_replace_tags_success(self, mock_get_client):
        mock_get_client.return_value = self.mock_client

        tag_op = TagOperations(
            operation=TagOperation.REPLACE,
            tag_names=["Public"],
        )

        result = update_assets(
            updatable_assets=[self.asset1],
            attribute_name=UpdatableAttribute.TAG,
            attribute_values=[tag_op],
        )

        self.assertEqual(result["updated_count"], 1)
        self.assertEqual(len(result["errors"]), 0)
        self.mock_client.asset._modify_tags.assert_called_once()
        call_kwargs = self.mock_client.asset._modify_tags.call_args[1]
        self.assertEqual(call_kwargs["qualified_name"], self.asset1.qualified_name)
        self.assertEqual(call_kwargs["atlan_tag_names"], ["Public"])
        self.assertEqual(call_kwargs["modification_type"], "replace")
        self.assertEqual(
            call_kwargs["save_parameters"],
            {"replace_atlan_tags": True, "append_atlan_tags": False},
        )

    @patch("tools.assets.get_atlan_client")
    def test_tag_validation_non_existent_tag(self, mock_get_client):
        mock_get_client.return_value = self.mock_client

        tag_op = TagOperations(
            operation=TagOperation.ADD,
            tag_names=["NonExistentTag", "PII", "AnotherFakeTag"],
        )

        result = update_assets(
            updatable_assets=[self.asset1],
            attribute_name=UpdatableAttribute.TAG,
            attribute_values=[tag_op],
        )

        self.assertEqual(result["updated_count"], 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("NonExistentTag", result["errors"][0])
        self.assertIn("AnotherFakeTag", result["errors"][0])
        self.assertIn("do not exist in the system", result["errors"][0])
        # Ensure add_atlan_tags was NOT called
        self.mock_client.asset.add_atlan_tags.assert_not_called()

    @patch("tools.assets.get_atlan_client")
    def test_bulk_update_multiple_assets(self, mock_get_client):
        mock_get_client.return_value = self.mock_client

        tag_op1 = TagOperations(
            operation=TagOperation.ADD,
            tag_names=["PII"],
        )
        tag_op2 = TagOperations(
            operation=TagOperation.REPLACE,
            tag_names=["Public"],
        )

        result = update_assets(
            updatable_assets=[self.asset1, self.asset2],
            attribute_name=UpdatableAttribute.TAG,
            attribute_values=[tag_op1, tag_op2],
        )

        self.assertEqual(result["updated_count"], 2)
        self.assertEqual(len(result["errors"]), 0)
        self.mock_client.asset.add_atlan_tags.assert_called_once()
        self.mock_client.asset._modify_tags.assert_called_once()

    @patch("tools.assets.get_atlan_client")
    def test_invalid_tag_operations_type(self, mock_get_client):
        mock_get_client.return_value = self.mock_client

        result = update_assets(
            updatable_assets=[self.asset1],
            attribute_name=UpdatableAttribute.TAG,
            attribute_values=["invalid_string_value"],
        )

        self.assertEqual(result["updated_count"], 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("Tag value must be a TagOperations object", result["errors"][0])

    @patch("tools.assets.get_atlan_client")
    def test_api_exception_handling(self, mock_get_client):
        mock_get_client.return_value = self.mock_client
        self.mock_client.asset.add_atlan_tags.side_effect = Exception("Atlan API error")

        tag_op = TagOperations(
            operation=TagOperation.ADD,
            tag_names=["PII"],
        )

        result = update_assets(
            updatable_assets=[self.asset1],
            attribute_name=UpdatableAttribute.TAG,
            attribute_values=[tag_op],
        )

        self.assertEqual(result["updated_count"], 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("Atlan API error", result["errors"][0])

    @patch("tools.assets.get_atlan_client")
    def test_update_assets_with_dict_value(self, mock_get_client):
        mock_get_client.return_value = self.mock_client

        tag_dict = {
            "operation": "add",
            "tag_names": ["PII"],
        }

        result = update_assets(
            updatable_assets=[self.asset1],
            attribute_name=UpdatableAttribute.TAG,
            attribute_values=[tag_dict],
        )

        self.assertEqual(result["updated_count"], 1)
        self.assertEqual(len(result["errors"]), 0)
        self.mock_client.asset.add_atlan_tags.assert_called_once()

    @patch("tools.assets.get_atlan_client")
    def test_empty_tag_names_error(self, mock_get_client):
        mock_get_client.return_value = self.mock_client

        tag_op = TagOperations(
            operation=TagOperation.ADD,
            tag_names=[],
        )

        result = update_assets(
            updatable_assets=[self.asset1],
            attribute_name=UpdatableAttribute.TAG,
            attribute_values=[tag_op],
        )

        self.assertEqual(result["updated_count"], 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("Atleast one tag name must be provided" if "Atleast" in result["errors"][0] else "At least one tag name must be provided", result["errors"][0])


class TestServerUpdateAssetsToolWithTags(unittest.TestCase):
    """Unit tests for server.py update_assets_tool with tag attribute."""

    @patch("server.update_assets")
    def test_server_tool_tag_dict_parsing(self, mock_update_assets):
        mock_update_assets.return_value = {"updated_count": 1, "errors": []}

        asset_dict = {
            "guid": "guid-123",
            "name": "CustomerTable",
            "type_name": "Table",
            "qualified_name": "default/snowflake/123/CUSTOMER_TABLE",
        }
        tag_dict = {
            "operation": "add",
            "tag_names": ["PII", "Confidential"],
            "propagate": True,
        }

        tool_fn = getattr(update_assets_tool, "fn", update_assets_tool)
        result = tool_fn(
            assets=asset_dict,
            attribute_name="tag",
            attribute_values=[tag_dict],
        )

        self.assertEqual(result["updated_count"], 1)
        mock_update_assets.assert_called_once()
        call_kwargs = mock_update_assets.call_args[1]
        self.assertEqual(call_kwargs["attribute_name"], UpdatableAttribute.TAG)
        self.assertEqual(len(call_kwargs["attribute_values"]), 1)
        self.assertIsInstance(call_kwargs["attribute_values"][0], TagOperations)
        self.assertEqual(call_kwargs["attribute_values"][0].operation, TagOperation.ADD)
        self.assertEqual(call_kwargs["attribute_values"][0].tag_names, ["PII", "Confidential"])
        self.assertTrue(call_kwargs["attribute_values"][0].propagate)

    def test_server_tool_invalid_tag_value(self):
        asset_dict = {
            "guid": "guid-123",
            "name": "CustomerTable",
            "type_name": "Table",
            "qualified_name": "default/snowflake/123/CUSTOMER_TABLE",
        }

        tool_fn = getattr(update_assets_tool, "fn", update_assets_tool)
        result = tool_fn(
            assets=asset_dict,
            attribute_name="tag",
            attribute_values=["invalid_non_dict_value"],
        )

        self.assertEqual(result["updated_count"], 0)
        self.assertIn("error", result)
        self.assertIn("Tag attribute values must be dictionaries", result["error"])


if __name__ == "__main__":
    unittest.main()

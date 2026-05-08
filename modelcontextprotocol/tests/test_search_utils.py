import unittest

from pyatlan.model.assets import Asset

from utils.search import SearchUtils


class SearchUtilsTests(unittest.TestCase):
    def test_contains_falls_back_to_match_for_atlan_text_fields(self):
        condition = SearchUtils._apply_operator_condition(
            Asset.NAME,
            "contains",
            "customers",
        )

        self.assertIsNotNone(condition)

    def test_contains_prefers_native_contains_when_available(self):
        class ContainsField:
            def contains(self, value, case_insensitive=False):
                return {
                    "operator": "contains",
                    "value": value,
                    "case_insensitive": case_insensitive,
                }

        condition = SearchUtils._apply_operator_condition(
            ContainsField(),
            "contains",
            "customers",
            case_insensitive=True,
        )

        self.assertEqual(
            condition,
            {
                "operator": "contains",
                "value": "customers",
                "case_insensitive": True,
            },
        )

    def test_contains_raises_value_error_when_unsupported(self):
        with self.assertRaisesRegex(ValueError, "contains"):
            SearchUtils._apply_operator_condition(object(), "contains", "customers")

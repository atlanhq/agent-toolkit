"""Unit tests for SearchUtils substring-wildcard rewriting.

The substring rewrite serves leading-wildcard name searches ("*ACCOUNT_MANAGER*")
from the analyzed sibling fields instead of a term-dictionary scan. These tests
pin which patterns and fields are rewritten and which fall through to a plain
wildcard, so the narrow rule can't widen or drift by accident.

search.py is loaded directly by path: importing the utils package eagerly pulls in
client/settings, which need environment configuration this unit test shouldn't require.
"""

import importlib.util
from pathlib import Path

import pytest
from pyatlan.model.assets import Asset
from pyatlan.model.search import Bool, MatchPhrase, Prefix, Term, Wildcard

_SEARCH_PATH = Path(__file__).resolve().parent.parent / "utils" / "search.py"
_spec = importlib.util.spec_from_file_location("search_under_test", _SEARCH_PATH)
_search = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_search)
SearchUtils = _search.SearchUtils


def _phrase_fields(condition):
    """Field names a rewritten Bool phrase-matches against."""
    assert isinstance(condition, Bool)
    assert condition.minimum_should_match == 1
    assert all(isinstance(c, MatchPhrase) for c in condition.should)
    return [c.field for c in condition.should]


# ---------------------------------------------------------------------------
# _analyzed_siblings — the fields a name is phrase-matched against
# ---------------------------------------------------------------------------


class TestAnalyzedSiblings:
    def test_name_includes_text_delimiter_and_stemmed(self):
        assert SearchUtils._analyzed_siblings(Asset.NAME) == [
            "name",
            "name.delimiter",
            "name.stemmed",
        ]

    def test_display_name_dedupes_to_the_delimiter_sibling(self):
        # pyatlan models displayName's analyzed field AS displayName.delimiter and
        # exposes no stemmed sibling, so the set collapses to one entry.
        assert SearchUtils._analyzed_siblings(Asset.DISPLAY_NAME) == [
            "displayName.delimiter"
        ]


# ---------------------------------------------------------------------------
# _rewrite_substring_wildcard — pattern + field gating
# ---------------------------------------------------------------------------


class TestRewriteSubstringWildcard:
    @pytest.mark.parametrize(
        "pattern",
        ["*ACCOUNT_MANAGER*", "*MANAGER", "*data_version*", "*MANAGER*"],
    )
    def test_substring_patterns_on_name_are_rewritten(self, pattern):
        # Single-token ("*MANAGER*") is rewritten too: the delimiter/stemmed siblings
        # carry the recall, so the rule is not restricted to delimited substrings.
        cond = SearchUtils._rewrite_substring_wildcard(Asset.NAME, pattern)
        assert _phrase_fields(cond) == ["name", "name.delimiter", "name.stemmed"]

    @pytest.mark.parametrize(
        "pattern",
        [
            "ACCOUNT_ID*",  # prefix — already seeks into the term dictionary
            "*ACC*MGR*",  # interior "*" — a phrase can't express it
            "*A?C*",  # interior "?" — same
            "**",  # no substring
            "*   *",  # whitespace-only substring
            "plain_no_stars",  # not a wildcard pattern at all
        ],
    )
    def test_non_substring_patterns_are_not_rewritten(self, pattern):
        assert SearchUtils._rewrite_substring_wildcard(Asset.NAME, pattern) is None

    @pytest.mark.parametrize("field", ["QUALIFIED_NAME", "OWNER_USERS"])
    def test_non_name_fields_are_not_rewritten(self, field):
        cond = SearchUtils._rewrite_substring_wildcard(getattr(Asset, field), "*abc*")
        assert cond is None

    def test_non_string_value_is_not_rewritten(self):
        assert SearchUtils._rewrite_substring_wildcard(Asset.NAME, ["*abc*"]) is None

    def test_leading_and_trailing_stars_are_stripped_from_the_term(self):
        cond = SearchUtils._rewrite_substring_wildcard(Asset.NAME, "**ACCOUNT**")
        assert all(c.query == "ACCOUNT" for c in cond.should)


# ---------------------------------------------------------------------------
# _apply_operator_condition — the wildcard operator branch
# ---------------------------------------------------------------------------


class TestWildcardOperator:
    def test_substring_on_name_is_served_as_a_phrase(self):
        cond = SearchUtils._apply_operator_condition(Asset.NAME, "wildcard", "*mgr*")
        assert _phrase_fields(cond) == ["name", "name.delimiter", "name.stemmed"]

    def test_prefix_stays_a_wildcard(self):
        cond = SearchUtils._apply_operator_condition(Asset.NAME, "wildcard", "ACCOUNT*")
        assert isinstance(cond, Wildcard) and cond.value == "ACCOUNT*"

    def test_interior_wildcard_stays_a_wildcard(self):
        cond = SearchUtils._apply_operator_condition(Asset.NAME, "wildcard", "*a*b*")
        assert isinstance(cond, Wildcard) and cond.value == "*a*b*"

    def test_qualified_name_substring_stays_a_wildcard(self):
        cond = SearchUtils._apply_operator_condition(
            Asset.QUALIFIED_NAME, "wildcard", "*default/snow*"
        )
        assert isinstance(cond, Wildcard) and cond.value == "*default/snow*"


# ---------------------------------------------------------------------------
# _apply_operator_condition — the contains operator branch
# ---------------------------------------------------------------------------


class TestContainsOperator:
    def test_contains_on_name_is_served_as_a_phrase(self):
        # KeywordText fields expose no .contains(); contains is routed through the
        # substring path instead of raising AttributeError.
        cond = SearchUtils._apply_operator_condition(
            Asset.NAME, "contains", "ACCOUNT_MANAGER"
        )
        assert _phrase_fields(cond) == ["name", "name.delimiter", "name.stemmed"]

    def test_contains_on_identifier_field_falls_back_to_a_wildcard(self):
        cond = SearchUtils._apply_operator_condition(
            Asset.QUALIFIED_NAME, "contains", "snow"
        )
        assert isinstance(cond, Wildcard) and cond.value == "*snow*"

    def test_contains_rejects_non_string_values(self):
        with pytest.raises(ValueError):
            SearchUtils._apply_operator_condition(Asset.NAME, "contains", 123)


# ---------------------------------------------------------------------------
# Unrelated operators are untouched by the rewrite
# ---------------------------------------------------------------------------


class TestOtherOperatorsUnchanged:
    def test_eq_is_a_term(self):
        cond = SearchUtils._apply_operator_condition(Asset.NAME, "eq", "x")
        assert isinstance(cond, Term)

    def test_startswith_is_a_prefix(self):
        cond = SearchUtils._apply_operator_condition(Asset.NAME, "startswith", "x")
        assert isinstance(cond, Prefix)

    def test_unknown_operator_raises(self):
        with pytest.raises(ValueError):
            SearchUtils._apply_operator_condition(Asset.NAME, "nope", "x")

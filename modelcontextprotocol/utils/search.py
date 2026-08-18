from typing import Dict, Any, Optional
import logging
import re
from pyatlan.model.assets import Asset
from pyatlan.model.search import Bool, MatchPhrase

logger = logging.getLogger(__name__)

# Matches a pattern that is a plain substring wrapped in leading/trailing "*", e.g.
# "*ACCOUNT_MANAGER*" or "*MANAGER". Patterns with interior "*"/"?" are left alone
# because a phrase match cannot express them.
_SUBSTRING_WILDCARD = re.compile(r"^\*+(?P<term>[^*?]+?)\**$")

# Only human-readable name fields are rewritten. Identifier-shaped fields are excluded
# deliberately: a qualifiedName is a path, and matching it through an analyzer loses the
# anchor — "*vJm9k6ARmG" returns 1 document as a wildcard and 155 as a phrase, because
# the analyzer splits the id into tokens that then match anywhere in the path.
_SUBSTRING_REWRITE_FIELDS = frozenset({"name", "displayName"})


class SearchUtils:
    @staticmethod
    def process_results(results: Any) -> Dict[str, Any]:
        """
        Process the results from the search index using Pydantic serialization.

        This method uses Pydantic's .dict(by_alias=True, exclude_unset=True) to:
        - Convert field names to their API-friendly camelCase format (by_alias=True)
        - Exclude any fields that weren't explicitly set (exclude_unset=True)

        Args:
            results: The search results from Atlan

        Returns:
            Dict[str, Any]: Dictionary containing:
                - results: List of processed results
                - aggregations: Search aggregations if available
                - error: None if no error occurred, otherwise the error message
        """
        current_page_results = (
            results.current_page()
            if hasattr(results, "current_page") and callable(results.current_page)
            else []
        )
        aggregations = results.aggregations

        logger.info(f"Processing {len(current_page_results)} search results")
        results_list = [
            result.dict(by_alias=True, exclude_unset=True)
            for result in current_page_results
            if result is not None
        ]

        return {"results": results_list, "aggregations": aggregations, "error": None}

    @staticmethod
    def _get_asset_attribute(attr_name: str):
        """
        Get Asset attribute by name.
        """
        return getattr(Asset, attr_name.upper(), None)

    @staticmethod
    def _analyzed_siblings(attr) -> list:
        """
        Analyzed fields to phrase-match a name against, most specific first.

        The delimiter sibling is what makes a single-token substring work: it indexes
        each token, the whole delimited string, and the concatenation, so "MANAGER"
        still reaches "ACCOUNT_MANAGER". Without it recall drops to 75% (2,939 of 3,902
        documents on a production index). A sibling that does not exist on the index
        simply matches nothing, so listing it is safe.
        """
        base = getattr(attr, "atlan_field_name", None)
        fields = []
        for candidate in (
            getattr(attr, "text_field_name", None),
            f"{base}.delimiter" if base else None,
            getattr(attr, "stemmed_field_name", None),
        ):
            if candidate and candidate not in fields:
                fields.append(candidate)
        return fields

    @staticmethod
    def _substring_phrase(attr, term: str) -> Optional[Any]:
        """
        Phrase-match a plain substring against a name field's analyzed siblings, or None
        when the field is not an eligible name field or exposes no analyzed sibling.

        A leading-"*" wildcard cannot seek into the term dictionary, so Lucene enumerates
        every term for the field and tests each one; the cost scales with catalog size
        rather than with the number of matches, so it degrades as a tenant grows. Phrasing
        the same text against the analyzed siblings is served by the inverted index
        instead, and also matches inputs the wildcard misses entirely: "account manager"
        finds nothing as a wildcard and all 348 documents as a phrase, because the analyzer
        folds case and delimiters. The delimiter sibling is what lets a single-token
        substring ("MANAGER") still reach a delimited name ("ACCOUNT_MANAGER").

        Only human-readable name fields are eligible (_SUBSTRING_REWRITE_FIELDS);
        identifier-shaped fields like qualifiedName are excluded because analyzing a path
        loses the anchor.
        """
        if not isinstance(term, str) or not term.strip():
            return None
        if getattr(attr, "atlan_field_name", None) not in _SUBSTRING_REWRITE_FIELDS:
            return None
        fields = SearchUtils._analyzed_siblings(attr)
        if not fields:
            return None
        return Bool(
            should=[MatchPhrase(field=field, query=term) for field in fields],
            minimum_should_match=1,
        )

    @staticmethod
    def _rewrite_substring_wildcard(attr, value: Any) -> Optional[Any]:
        """
        Return a phrase-match condition equivalent to a plain substring wildcard, or None
        when the pattern or the field cannot be rewritten safely.

        Rewriting is skipped when the pattern contains interior wildcards (a phrase match
        cannot express those) and when it only anchors a prefix such as "ACCOUNT*" — those
        already seek directly into the term dictionary. Field eligibility and the analyzed
        siblings are decided by _substring_phrase.
        """
        if not isinstance(value, str):
            return None
        matched = _SUBSTRING_WILDCARD.match(value)
        if not matched:
            return None
        return SearchUtils._substring_phrase(attr, matched.group("term").strip())

    @staticmethod
    def _apply_operator_condition(
        attr, operator: str, value: Any, case_insensitive: bool = False
    ):
        """
        Apply an operator condition to an attribute.

        Args:
            attr: The Asset attribute object
            operator (str): The operator to apply
            value: The value for the condition
            case_insensitive (bool): Whether to apply case insensitive matching

        Returns:
            The condition object to be used with where/where_not/where_some

        Raises:
            ValueError: If the operator is unknown or value format is invalid
        """
        logger.debug(
            f"Applying operator '{operator}' with value '{value}' (case_insensitive={case_insensitive})"
        )

        if operator == "startswith":
            return attr.startswith(value, case_insensitive=case_insensitive)
        elif operator == "match":
            return attr.match(value)
        elif operator == "eq":
            return attr.eq(value, case_insensitive=case_insensitive)
        elif operator == "neq":
            return attr.neq(value, case_insensitive=case_insensitive)
        elif operator == "gte":
            return attr.gte(value)
        elif operator == "lte":
            return attr.lte(value)
        elif operator == "gt":
            return attr.gt(value)
        elif operator == "lt":
            return attr.lt(value)
        elif operator == "has_any_value":
            return attr.has_any_value()
        elif operator == "contains":
            # "contains" is a substring match, i.e. the same intent as wildcard "*value*".
            # pyatlan's KeywordText fields expose no .contains(), so calling it raised
            # AttributeError; route through the same path instead. Name fields are served
            # from the analyzed siblings (fast); other fields fall back to a "*value*"
            # wildcard, which is what contains means.
            if not isinstance(value, str):
                raise ValueError(
                    f"Invalid value for 'contains' operator: {value}, expected a string"
                )
            phrase = SearchUtils._substring_phrase(attr, value)
            if phrase is not None:
                logger.info(
                    f"Served 'contains' on "
                    f"'{getattr(attr, 'atlan_field_name', '?')}' as a phrase match"
                )
                return phrase
            return attr.wildcard(f"*{value}*")
        elif operator == "wildcard":
            rewritten = SearchUtils._rewrite_substring_wildcard(attr, value)
            if rewritten is not None:
                logger.info(
                    f"Rewrote substring wildcard '{value}' on "
                    f"'{getattr(attr, 'atlan_field_name', '?')}' to a phrase match"
                )
                return rewritten
            return attr.wildcard(value)
        elif operator == "between":
            # Expecting value to be a list/tuple with [start, end]
            if isinstance(value, (list, tuple)) and len(value) == 2:
                return attr.between(value[0], value[1])
            else:
                raise ValueError(
                    f"Invalid value format for 'between' operator: {value}, expected [start, end]"
                )
        else:
            # Try to get the operator method from the attribute
            op_method = getattr(attr, operator, None)
            if op_method is None:
                raise ValueError(f"Unknown operator: {operator}")

            # Try to pass case_insensitive if the method supports it
            try:
                return op_method(value, case_insensitive=case_insensitive)
            except TypeError:
                # Fallback if case_insensitive is not supported
                return op_method(value)

    @staticmethod
    def _process_condition(
        search, attr, condition, attr_name: str, search_method_name: str
    ):
        """
        Process a single condition and apply it to the search using the specified method.

        Args:
            search: The FluentSearch object
            attr: The Asset attribute object
            condition: The condition value (dict, list, or simple value)
            attr_name (str): The attribute name for logging
            search_method_name (str): The search method to use ('where', 'where_not', 'where_some')

        Returns:
            FluentSearch: The updated search object
        """
        search_method = getattr(search, search_method_name)

        if isinstance(condition, dict):
            operator = condition.get("operator", "eq")
            value = condition.get("value")
            case_insensitive = condition.get("case_insensitive", False)

            try:
                condition_obj = SearchUtils._apply_operator_condition(
                    attr, operator, value, case_insensitive
                )
                search = search_method(condition_obj)
                return search
            except ValueError as e:
                logger.warning(f"Skipping condition for {attr_name}: {e}")
                return search
        elif isinstance(condition, list):
            if search_method_name == "where_some":
                # Handle multiple values for where_some
                logger.debug(
                    f"Adding multiple '{search_method_name}' values for {attr_name}: {condition}"
                )
                for value in condition:
                    search = search_method(attr.eq(value))
                return search
            else:
                # Handle list of values with OR logic using .within()
                logger.debug(f"Applying multiple values for {attr_name}: {condition}")
                search = search_method(attr.within(condition))
                return search
        elif condition == "has_any_value" and search_method_name == "where_not":
            # Special case for has_any_value in negative conditions
            logger.debug(f"Excluding assets where {attr_name} has any value")
            search = search_method(attr.has_any_value())
            return search
        else:
            # Default to equality operator
            logger.debug(
                f"Applying {search_method_name} equality condition {attr_name}={condition}"
            )
            search = search_method(attr.eq(condition))
            return search

from typing import Dict, Any
import logging
from pyatlan.model.assets import Asset

logger = logging.getLogger(__name__)


class SearchUtils:
    OPERATOR_MAP = {
        "eq": lambda attr, v, ci: attr.eq(v, case_insensitive=ci),
        "neq": lambda attr, v, ci: attr.neq(v, case_insensitive=ci),
        "startswith": lambda attr, v, ci: attr.startswith(v, case_insensitive=ci),
        "contains": lambda attr, v, ci: attr.contains(v, case_insensitive=ci),
        "lt": lambda attr, v: attr.lt(v),
        "lte": lambda attr, v: attr.lte(v),
        "gt": lambda attr, v: attr.gt(v),
        "gte": lambda attr, v: attr.gte(v),
        "match": lambda attr, v: attr.match(v),
        "has_any_value": lambda attr: attr.has_any_value(),
    }
    
    CASE_INSENSITIVE_OPS = {"lt", "lte", "gt", "gte", "match"}
    NO_VALUE_OPS = {"has_any_value"}
    
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

        # Special case for between - needs custom handling
        if operator == "between":
            # Expecting value to be a list/tuple with [start, end]
            if isinstance(value, (list, tuple)) and len(value) == 2:
                return attr.between(value[0], value[1])
            else:
                raise ValueError(
                    f"Invalid value format for 'between' operator: {value}, expected [start, end]"
                )

        if operator in SearchUtils.OPERATOR_MAP:
            op_func = SearchUtils.OPERATOR_MAP[operator]
            # Handle operators that don't need value or case_insensitive
            if operator in SearchUtils.NO_VALUE_OPS:
                return op_func(attr)
            elif operator in SearchUtils.CASE_INSENSITIVE_OPS:
                return op_func(attr, value)
            else:
                return op_func(attr, value, case_insensitive)

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

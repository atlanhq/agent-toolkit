import logging
import json
from typing import Type, List, Optional, Union, Dict, Any

from client import get_atlan_client
from pyatlan.model.assets import Asset
from pyatlan.model.fluent_search import CompoundQuery, FluentSearch
from pyatlan.model.fields.atlan_fields import AtlanField

# Configure logging
logger = logging.getLogger(__name__)


def _apply_positive_conditions(search_builder: FluentSearch, conditions_data: Union[Dict[str, Any], str], asset_model: Type[Asset]) -> FluentSearch:
    """Helper function to apply positive conditions to the FluentSearch builder."""
    processed_conditions = conditions_data
    if isinstance(conditions_data, str):
        try:
            processed_conditions = json.loads(conditions_data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse conditions JSON: {e}")
            logger.debug(f"Invalid JSON string: {conditions_data}")
            raise ValueError(f"Invalid JSON in conditions parameter: {e}")
    
    if not isinstance(processed_conditions, dict):
        # This case should ideally not be reached if input is string or dict as per type hints
        # but as a safeguard if conditions_data was a string that didn't parse to a dict.
        logger.warning("Conditions could not be processed into a dictionary, skipping positive conditions.")
        return search_builder

    logger.debug(f"Applying positive conditions: {processed_conditions}")
    condition_count = 0
    for attr_name, condition_value in processed_conditions.items():
        attr_field = getattr(asset_model, attr_name.upper(), None)
        if attr_field is None:
            logger.warning(f"Unknown attribute: {attr_name}, skipping condition")
            continue

        logger.debug(f"Processing condition for attribute: {attr_name}")

        if isinstance(condition_value, dict):
            operator = condition_value.get("operator", "eq")
            value = condition_value.get("value")
            logger.debug(f"Applying operator '{operator}' with value '{value}'")

            op_method = getattr(attr_field, operator, None)
            if op_method:
                if operator == "has_any_value": # Methods like has_any_value take no arguments
                    search_builder = search_builder.where(op_method())
                else:
                    search_builder = search_builder.where(op_method(value))
            else:
                logger.warning(f"Unknown operator: {operator} for attribute {attr_name}, skipping condition")
                continue
        elif isinstance(condition_value, list):
            logger.debug(f"Applying multiple equality conditions (AND logic) for {attr_name}: {condition_value}")
            for val in condition_value:
                search_builder = search_builder.where(attr_field.eq(val))
        else:
            logger.debug(f"Applying equality condition {attr_name}={condition_value}")
            search_builder = search_builder.where(attr_field.eq(condition_value))
        condition_count += 1
    logger.debug(f"Applied {condition_count} positive conditions")
    return search_builder


def _apply_negative_conditions(search_builder: FluentSearch, conditions_data: Dict[str, Any], asset_model: Type[Asset]) -> FluentSearch:
    """Helper function to apply negative conditions to the FluentSearch builder."""
    logger.debug(f"Applying negative conditions: {conditions_data}")
    neg_condition_count = 0
    for attr_name, condition_value in conditions_data.items():
        attr_field = getattr(asset_model, attr_name.upper(), None)
        if attr_field is None:
            logger.warning(f"Unknown attribute for negative condition: {attr_name}, skipping")
            continue

        logger.debug(f"Processing negative condition for attribute: {attr_name}")

        if isinstance(condition_value, dict):
            operator = condition_value.get("operator", "eq")
            value = condition_value.get("value")
            logger.debug(f"Applying negative operator '{operator}' with value '{value}'")

            op_method = getattr(attr_field, operator, None)
            if op_method:
                if operator == "has_any_value": # Methods like has_any_value take no arguments
                    search_builder = search_builder.where_not(op_method())
                else:
                    search_builder = search_builder.where_not(op_method(value))
            else:
                logger.warning(f"Unknown operator for negative condition: {operator}, skipping")
                continue
        elif condition_value == "has_any_value":
            logger.debug(f"Excluding assets where {attr_name} has any value")
            search_builder = search_builder.where_not(attr_field.has_any_value())
        else:
            logger.debug(f"Excluding assets where {attr_name}={condition_value}")
            search_builder = search_builder.where_not(attr_field.eq(condition_value))
        neg_condition_count += 1
    logger.debug(f"Applied {neg_condition_count} negative conditions")
    return search_builder


def _apply_some_conditions(search_builder: FluentSearch, conditions_data: Dict[str, Any], min_somes_count: int, asset_model: Type[Asset]) -> FluentSearch:
    """Helper function to apply 'some' conditions to the FluentSearch builder."""
    logger.debug(f"Applying 'some' conditions: {conditions_data} with min_somes={min_somes_count}")
    some_condition_clauses = [] # Collect individual .eq() clauses here
    applied_some_conditions_count = 0

    for attr_name, condition_value in conditions_data.items():
        attr_field = getattr(asset_model, attr_name.upper(), None)
        if attr_field is None:
            logger.warning(f"Unknown attribute for 'some' condition: {attr_name}, skipping")
            continue

        logger.debug(f"Processing 'some' condition for attribute: {attr_name}")

        if isinstance(condition_value, list):
            logger.debug(f"Adding multiple 'some' values for {attr_name}: {condition_value}")
            for value_item in condition_value:
                # Each condition for where_some should be a complete query part, like AtlanField.eq(value)
                some_condition_clauses.append(attr_field.eq(value_item))
                applied_some_conditions_count += 1
        else:
            logger.debug(f"Adding 'some' condition {attr_name}={condition_value}")
            some_condition_clauses.append(attr_field.eq(condition_value))
            applied_some_conditions_count += 1

    if some_condition_clauses:
        search_builder = search_builder.where_some(some_condition_clauses)
        logger.debug(f"Setting min_somes={min_somes_count} for {applied_some_conditions_count} 'some' conditions")
        search_builder = search_builder.min_somes(min_somes_count)
    
    return search_builder


def _apply_date_range_filters(search_builder: FluentSearch, date_range_data: Dict[str, Dict[str, Any]], asset_model: Type[Asset]) -> FluentSearch:
    """Helper function to apply date range filters to the FluentSearch builder."""
    logger.debug(f"Applying date range filters: {date_range_data}")
    date_range_condition_count = 0
    for attr_name, range_conditions in date_range_data.items():
        attr_field = getattr(asset_model, attr_name.upper(), None)
        if attr_field is None:
            logger.warning(f"Unknown attribute for date range: {attr_name}, skipping")
            continue

        logger.debug(f"Processing date range for attribute: {attr_name}")
        processed_any_range = False
        for operator, value in range_conditions.items():
            op_method = getattr(attr_field, operator, None)
            if op_method:
                logger.debug(f"Adding {attr_name} {operator} {value}")
                search_builder = search_builder.where(op_method(value))
                date_range_condition_count += 1
                processed_any_range = True
            else:
                # This dynamic version would support any valid AtlanField method name (e.g., eq, neq for dates if they exist)
                # We could restrict operators here.        
                # However, getattr failing for unsupported ops is safe.
                logger.warning(f"Unsupported operator '{operator}' for date range on attribute {attr_name}, skipping.")
        
        if processed_any_range:
             logger.debug(f"Applied date range conditions for attribute: {attr_name}")

    logger.debug(f"Applied {date_range_condition_count} total date range conditions")
    return search_builder


def _include_requested_attributes(search_builder: FluentSearch, attributes_to_include: List[Union[str, AtlanField]], asset_model: Type[Asset]) -> FluentSearch:
    """Helper function to include requested attributes in the search results."""
    logger.debug(f"Including attributes in results: {attributes_to_include}")
    included_count = 0
    for attr_spec in attributes_to_include:
        if isinstance(attr_spec, str):
            attr_field_obj = getattr(asset_model, attr_spec.upper(), None)
            if attr_field_obj is None:
                logger.warning(f"Unknown attribute for inclusion: {attr_spec}, skipping")
                continue
            logger.debug(f"Including attribute by name: {attr_spec}")
            search_builder = search_builder.include_on_results(attr_field_obj)
        elif isinstance(attr_spec, AtlanField): # Check if it's already an AtlanField instance
            logger.debug(f"Including attribute object: {attr_spec}")
            search_builder = search_builder.include_on_results(attr_spec)
        else:
            logger.warning(f"Invalid attribute specification for inclusion: {attr_spec}, skipping. Expected string or AtlanField.")
            continue
        included_count += 1
    logger.debug(f"Included {included_count} attributes in results")
    return search_builder


def _apply_sorting(search_builder: FluentSearch, sort_by_attr_name: Optional[str], sort_order_str: str, asset_model: Type[Asset]) -> FluentSearch:
    """Helper function to apply sorting to the FluentSearch builder."""
    if not sort_by_attr_name:
        return search_builder 

    sort_attr_field = getattr(asset_model, sort_by_attr_name.upper(), None)
    if sort_attr_field is not None:
        if sort_order_str.upper() == "DESC":
            logger.debug(f"Setting sort order: {sort_by_attr_name} DESC")
            search_builder = search_builder.sort_by_desc(sort_attr_field)
        else:
            logger.debug(f"Setting sort order: {sort_by_attr_name} ASC")
            search_builder = search_builder.sort_by_asc(sort_attr_field)
    else:
        logger.warning(f"Unknown attribute for sorting: {sort_by_attr_name}, skipping sort")
    return search_builder


def search_assets(
    conditions: Optional[Union[Dict[str, Any], str]] = None,
    negative_conditions: Optional[Dict[str, Any]] = None,
    some_conditions: Optional[Dict[str, Any]] = None,
    min_somes: int = 1,
    include_attributes: Optional[List[Union[str, AtlanField]]] = None,
    asset_type: Optional[Union[Type[Asset], str]] = None,
    include_archived: bool = False,
    limit: int = 10,
    offset: int = 0,
    sort_by: Optional[str] = None,
    sort_order: str = "ASC",
    connection_qualified_name: Optional[str] = None,
    tags: Optional[List[str]] = None,
    directly_tagged: bool = True,
    domain_guids: Optional[List[str]] = None,
    date_range: Optional[Dict[str, Dict[str, Any]]] = None,
    guids: Optional[List[str]] = None,
) -> List[Asset]:
    """
    Advanced asset search using FluentSearch with flexible conditions.

    Args:
        conditions (Dict[str, Any], optional): Dictionary of attribute conditions to match.
            Format: {"attribute_name": value} or {"attribute_name": {"operator": operator, "value": value}}
        negative_conditions (Dict[str, Any], optional): Dictionary of attribute conditions to exclude.
            Format: {"attribute_name": value} or {"attribute_name": {"operator": operator, "value": value}}
        some_conditions (Dict[str, Any], optional): Conditions for where_some() queries that require min_somes of them to match.
            Format: {"attribute_name": value} or {"attribute_name": {"operator": operator, "value": value}}
        min_somes (int): Minimum number of some_conditions that must match. Defaults to 1.
        include_attributes (List[Union[str, AtlanField]], optional): List of specific attributes to include in results.
            Can be string attribute names or AtlanField objects.
        asset_type (Union[Type[Asset], str], optional): Type of asset to search for.
            Either a class (e.g., Table, Column) or a string type name (e.g., "Table", "Column")
        include_archived (bool): Whether to include archived assets. Defaults to False.
        limit (int, optional): Maximum number of results to return. Defaults to 10.
        offset (int, optional): Offset for pagination. Defaults to 0.
        sort_by (str, optional): Attribute to sort by. Defaults to None.
        sort_order (str, optional): Sort order, "ASC" or "DESC". Defaults to "ASC".
        connection_qualified_name (str, optional): Connection qualified name to filter by.
        tags (List[str], optional): List of tags to filter by.
        directly_tagged (bool): Whether to filter for directly tagged assets only. Defaults to True.
        domain_guids (List[str], optional): List of domain GUIDs to filter by.
        date_range (Dict[str, Dict[str, Any]], optional): Date range filters.
            Format: {"attribute_name": {"gte": start_timestamp, "lte": end_timestamp}}
        guids (List[str], optional): List of GUIDs to filter by.


    Returns:
        List[Asset]: List of assets matching the search criteria

    Raises:
        Exception: If there's an error executing the search
    """
    logger.info(
        f"Starting asset search with parameters: asset_type={asset_type}, "
        f"limit={limit}, include_archived={include_archived}"
    )
    logger.debug(
        f"Full search parameters: conditions={conditions}, "
        f"negative_conditions={negative_conditions}, some_conditions={some_conditions}, "
        f"include_attributes={include_attributes}, "
        f"connection_qualified_name={connection_qualified_name}, "
        f"tags={tags}, domain_guids={domain_guids}"
    )

    try:
        # Initialize FluentSearch
        logger.debug("Initializing FluentSearch object")
        search = FluentSearch()

        # Apply asset type filter if provided
        if asset_type:
            if isinstance(asset_type, str):
                # Handle string type name
                logger.debug(f"Filtering by asset type name: {asset_type}")
                search = search.where(Asset.TYPE_NAME.eq(asset_type))
            else:
                # Handle class type
                logger.debug(f"Filtering by asset class: {asset_type.__name__}")
                search = search.where(CompoundQuery.asset_type(asset_type))

        # Filter for active assets unless archived are explicitly included
        if not include_archived:
            logger.debug("Filtering for active assets only")
            search = search.where(CompoundQuery.active_assets())

        # Apply connection qualified name filter if provided
        if connection_qualified_name:
            logger.debug(
                f"Filtering by connection qualified name: {connection_qualified_name}"
            )
            search = search.where(
                Asset.QUALIFIED_NAME.startswith(connection_qualified_name)
            )

        # Apply tags filter if provided
        if tags and len(tags) > 0:
            logger.debug(
                f"Filtering by tags: {tags}, directly_tagged={directly_tagged}"
            )
            search = search.where(
                CompoundQuery.tagged(with_one_of=tags, directly=directly_tagged)
            )

        # Apply domain GUIDs filter if provided
        if domain_guids and len(domain_guids) > 0:
            logger.debug(f"Filtering by domain GUIDs: {domain_guids}")
            for guid in domain_guids:
                search = search.where(Asset.DOMAIN_GUIDS.eq(guid))

        # Apply positive conditions
        if conditions:
            search = _apply_positive_conditions(search, conditions, Asset)

        # Apply negative conditions
        if negative_conditions:
            search = _apply_negative_conditions(search, negative_conditions, Asset)

        # Apply where_some conditions with min_somes
        if some_conditions:
            search = _apply_some_conditions(search, some_conditions, min_somes, Asset)

        # Apply date range filters
        if date_range:
            search = _apply_date_range_filters(search, date_range, Asset)

        if guids and len(guids) > 0:
            logger.debug(f"Applying GUID filter: {guids}")
            search = search.where(Asset.GUID.within(guids))

        # Include requested attributes
        if include_attributes:
            search = _include_requested_attributes(search, include_attributes, Asset)

        # Set pagination
        logger.debug(f"Setting pagination: limit={limit}, offset={offset}")
        search = search.page_size(limit)
        if offset > 0:
            search = search.from_offset(offset)

        # Set sorting
        search = _apply_sorting(search, sort_by, sort_order, Asset)

        # Execute search
        logger.debug("Converting FluentSearch to request object")
        request = search.to_request()

        # Log the request object if debug is enabled
        if logger.isEnabledFor(logging.DEBUG):
            request_json = json.dumps(request.to_json())
            logger.debug(f"Search request: {request_json}")

        logger.info("Executing search request")
        client = get_atlan_client()
        results = list(client.asset.search(request).current_page())

        logger.info(f"Search completed, returned {len(results)} results")

        return results
    except Exception as e:
        logger.error(f"Error searching assets: {str(e)}")
        logger.exception("Exception details:")
        return []

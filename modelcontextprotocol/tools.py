import logging
from typing import Type, List, Optional, TypeVar, Union, Dict, Any
import json

from client import create_atlan_client
from settings import Settings
from pyatlan.model.assets import Asset
from pyatlan.model.fluent_search import CompoundQuery, FluentSearch
from pyatlan.model.search import DSL, IndexSearchRequest
from pyatlan.model.fields.atlan_fields import AtlanField


# Configure logging
logger = logging.getLogger(__name__)
settings = Settings()
atlan_client = create_atlan_client(settings)

T = TypeVar("T", bound=Asset)


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
            if isinstance(conditions, str):
                try:
                    conditions = json.loads(conditions)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse conditions JSON: {e}")
                    logger.debug(f"Invalid JSON string: {conditions}")
                    raise ValueError(f"Invalid JSON in conditions parameter: {e}")
            logger.debug(f"Applying positive conditions: {conditions}")
            condition_count = 0
            for attr_name, condition in conditions.items():
                attr = getattr(Asset, attr_name.upper(), None)
                if attr is None:
                    logger.warning(
                        f"Unknown attribute: {attr_name}, skipping condition"
                    )
                    continue

                logger.debug(f"Processing condition for attribute: {attr_name}")

                if isinstance(condition, dict):
                    operator = condition.get("operator", "eq")
                    value = condition.get("value")

                    logger.debug(f"Applying operator '{operator}' with value '{value}'")

                    # Handle different operators
                    if operator == "startswith":
                        search = search.where(attr.startswith(value))
                    elif operator == "match":
                        search = search.where(attr.match(value))
                    elif operator == "eq":
                        search = search.where(attr.eq(value))
                    elif operator == "neq":
                        search = search.where(attr.neq(value))
                    elif operator == "gte":
                        search = search.where(attr.gte(value))
                    elif operator == "lte":
                        search = search.where(attr.lte(value))
                    elif operator == "gt":
                        search = search.where(attr.gt(value))
                    elif operator == "lt":
                        search = search.where(attr.lt(value))
                    elif operator == "has_any_value":
                        search = search.where(attr.has_any_value())
                    else:
                        op_method = getattr(attr, operator, None)
                        if op_method is None:
                            logger.warning(
                                f"Unknown operator: {operator}, skipping condition"
                            )
                            continue
                        search = search.where(op_method(value))
                elif isinstance(condition, list):
                    # Handle list of values with OR logic
                    logger.debug(
                        f"Applying multiple values for {attr_name}: {condition}"
                    )
                    for val in condition:
                        search = search.where(attr.eq(val))
                else:
                    # Default to equality operator
                    logger.debug(f"Applying equality condition {attr_name}={condition}")
                    search = search.where(attr.eq(condition))

                condition_count += 1

            logger.debug(f"Applied {condition_count} positive conditions")

        # Apply negative conditions
        if negative_conditions:
            logger.debug(f"Applying negative conditions: {negative_conditions}")
            neg_condition_count = 0
            for attr_name, condition in negative_conditions.items():
                attr = getattr(Asset, attr_name.upper(), None)
                if attr is None:
                    logger.warning(
                        f"Unknown attribute for negative condition: {attr_name}, skipping"
                    )
                    continue

                logger.debug(
                    f"Processing negative condition for attribute: {attr_name}"
                )

                if isinstance(condition, dict):
                    operator = condition.get("operator", "eq")
                    value = condition.get("value")

                    logger.debug(
                        f"Applying negative operator '{operator}' with value '{value}'"
                    )

                    if operator == "startswith":
                        search = search.where_not(attr.startswith(value))
                    elif operator == "contains":
                        search = search.where_not(attr.contains(value))
                    elif operator == "match":
                        search = search.where_not(attr.match(value))
                    elif operator == "eq":
                        search = search.where_not(attr.eq(value))
                    elif operator == "has_any_value":
                        search = search.where_not(attr.has_any_value())
                    else:
                        op_method = getattr(attr, operator, None)
                        if op_method is None:
                            logger.warning(
                                f"Unknown operator for negative condition: {operator}, skipping"
                            )
                            continue
                        search = search.where_not(op_method(value))
                elif condition == "has_any_value":
                    # Special case for has_any_value
                    logger.debug(f"Excluding assets where {attr_name} has any value")
                    search = search.where_not(attr.has_any_value())
                else:
                    # Default to equality operator
                    logger.debug(f"Excluding assets where {attr_name}={condition}")
                    search = search.where_not(attr.eq(condition))

                neg_condition_count += 1

            logger.debug(f"Applied {neg_condition_count} negative conditions")

        # Apply where_some conditions with min_somes
        if some_conditions:
            logger.debug(
                f"Applying 'some' conditions: {some_conditions} with min_somes={min_somes}"
            )
            some_condition_count = 0
            for attr_name, condition in some_conditions.items():
                attr = getattr(Asset, attr_name.upper(), None)
                if attr is None:
                    logger.warning(
                        f"Unknown attribute for 'some' condition: {attr_name}, skipping"
                    )
                    continue

                logger.debug(f"Processing 'some' condition for attribute: {attr_name}")

                if isinstance(condition, list):
                    # Handle multiple values for where_some
                    logger.debug(
                        f"Adding multiple 'some' values for {attr_name}: {condition}"
                    )
                    for value in condition:
                        search = search.where_some(attr.eq(value))
                        some_condition_count += 1
                else:
                    logger.debug(f"Adding 'some' condition {attr_name}={condition}")
                    search = search.where_some(attr.eq(condition))
                    some_condition_count += 1

            # Set minimum matches required
            logger.debug(
                f"Setting min_somes={min_somes} for {some_condition_count} 'some' conditions"
            )
            search = search.min_somes(min_somes)

        # Apply date range filters
        if date_range:
            logger.debug(f"Applying date range filters: {date_range}")
            date_range_count = 0
            for attr_name, range_cond in date_range.items():
                attr = getattr(Asset, attr_name.upper(), None)
                if attr is None:
                    logger.warning(
                        f"Unknown attribute for date range: {attr_name}, skipping"
                    )
                    continue

                logger.debug(f"Processing date range for attribute: {attr_name}")

                if "gte" in range_cond:
                    logger.debug(f"Adding {attr_name} >= {range_cond['gte']}")
                    search = search.where(attr.gte(range_cond["gte"]))
                    date_range_count += 1
                if "lte" in range_cond:
                    logger.debug(f"Adding {attr_name} <= {range_cond['lte']}")
                    search = search.where(attr.lte(range_cond["lte"]))
                    date_range_count += 1
                if "gt" in range_cond:
                    logger.debug(f"Adding {attr_name} > {range_cond['gt']}")
                    search = search.where(attr.gt(range_cond["gt"]))
                    date_range_count += 1
                if "lt" in range_cond:
                    logger.debug(f"Adding {attr_name} < {range_cond['lt']}")
                    search = search.where(attr.lt(range_cond["lt"]))
                    date_range_count += 1

            logger.debug(f"Applied {date_range_count} date range conditions")

        # Include requested attributes
        if include_attributes:
            logger.debug(f"Including attributes in results: {include_attributes}")
            included_count = 0
            for attr in include_attributes:
                if isinstance(attr, str):
                    attr_obj = getattr(Asset, attr.upper(), None)
                    if attr_obj is None:
                        logger.warning(
                            f"Unknown attribute for inclusion: {attr}, skipping"
                        )
                        continue
                    logger.debug(f"Including attribute: {attr}")
                    search = search.include_on_results(attr_obj)
                else:
                    # Assume it's already an AtlanField object
                    logger.debug(f"Including attribute object: {attr}")
                    search = search.include_on_results(attr)

                included_count += 1

            logger.debug(f"Included {included_count} attributes in results")

        # Set pagination
        logger.debug(f"Setting pagination: limit={limit}, offset={offset}")
        search = search.page_size(limit)
        if offset > 0:
            search = search.from_offset(offset)

        # Set sorting
        if sort_by:
            sort_attr = getattr(Asset, sort_by.upper(), None)
            if sort_attr is not None:
                if sort_order.upper() == "DESC":
                    logger.debug(f"Setting sort order: {sort_by} DESC")
                    search = search.sort_by_desc(sort_attr)
                else:
                    logger.debug(f"Setting sort order: {sort_by} ASC")
                    search = search.sort_by_asc(sort_attr)
            else:
                logger.warning(
                    f"Unknown attribute for sorting: {sort_by}, skipping sort"
                )

        # Execute search
        logger.debug("Converting FluentSearch to request object")
        request = search.to_request()

        # Log the request object if debug is enabled
        if logger.isEnabledFor(logging.DEBUG):
            request_json = json.dumps(request.to_json())
            logger.debug(f"Search request: {request_json}")

        logger.info("Executing search request")
        results = list(atlan_client.asset.search(request).current_page())

        logger.info(f"Search completed, returned {len(results)} results")

        return results
    except Exception as e:
        logger.error(f"Error searching assets: {str(e)}")
        logger.exception("Exception details:")
        return []


def get_assets_by_dsl(dsl_query: str) -> Dict[str, Any]:
    """
    Execute the search with the given query
    Args:
        dsl_query (required): The DSL object that is required to search the index.
    Returns:
        Dict[str, Any]: A dictionary containing the results and aggregations
    """
    logger.info("Starting DSL-based asset search")
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Processing DSL query string")
    try:
        # Parse string to dict if needed
        if isinstance(dsl_query, str):
            logger.debug("Converting DSL string to JSON")
            try:
                dsl_dict = json.loads(dsl_query)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in DSL query: {e}")
                return {
                    "results": [],
                    "aggregations": {},
                    "error": "Invalid JSON in DSL query",
                }

        logger.debug("Creating IndexSearchRequest")
        index_request = IndexSearchRequest(
            dsl=DSL(**dsl_dict),
            suppress_logs=True,
            show_search_score=True,
            exclude_meanings=False,
            exclude_atlan_tags=False,
        )

        logger.info("Executing DSL search request")
        results = atlan_client.asset.search(index_request)

        result_count = sum(1 for _ in results.current_page())
        logger.info(
            f"DSL search completed, returned approximately {result_count} results"
        )

        # Check if aggregations exist
        if hasattr(results, "aggregations") and results.aggregations:
            agg_count = len(results.aggregations)
            logger.debug(f"Search returned {agg_count} aggregations")
        else:
            logger.debug("Search returned no aggregations")

        return {"results": results, "aggregations": results.aggregations}
    except Exception as e:
        logger.error(f"Error in DSL search: {str(e)}")
        logger.exception("Exception details:")
        return {"results": [], "aggregations": {}, "error": str(e)}


def propagate_via_hierarchy(
    asset_guids: List[str], tag_names: List[str]
) -> Dict[str, Dict[str, Any]]:
    """
    Enable propagation of tags through hierarchy for a list of assets.

    Args:
        asset_guids (List[str]): List of GUIDs of assets to operate on
        tag_names (List[str]): List of tag names to propagate

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary with asset GUIDs as keys and
        operation results as values. Each result contains:
        - status: "success", "partial_success", or "error"
        - message: Summary of what happened
        - updated_tags: List of successfully updated tags
        - skipped_tags: List of tags that were already correct
        - failed_tags: List of failed tags with error details (if any)
        - error: Error message (if any)
        - error_type: Type of error (if any)
    """
    results = {}

    for asset_guid in asset_guids:
        try:
            logger.info(f"Processing asset: {asset_guid}")

            # Get the asset
            try:
                asset = atlan_client.asset.get_by_guid(asset_guid)
                if not asset:
                    error_msg = f"Asset not found: {asset_guid}"
                    logger.error(error_msg)
                    results[asset_guid] = {
                        "status": "error",
                        "message": error_msg,
                        "error": error_msg,
                        "error_type": "AssetNotFound",
                    }
                    continue
                logger.info(f"Successfully retrieved asset: {asset_guid}")
            except Exception as e:
                error_msg = f"Failed to get asset {asset_guid}: {str(e)}"
                logger.error(error_msg)
                results[asset_guid] = {
                    "status": "error",
                    "message": error_msg,
                    "error": str(e),
                    "error_type": "AssetRetrievalError",
                }
                continue

            # Track tags for this asset
            updated_tags = []
            skipped_tags = []
            failed_tags = []

            # Process each tag
            for tag_name in tag_names:
                try:
                    logger.info(f"Processing tag {tag_name} for asset {asset_guid}")

                    # Check if tag exists and get its properties
                    existing_tags = (
                        [tag.type_name for tag in asset.atlan_tags]
                        if asset.atlan_tags
                        else []
                    )
                    tag_exists = tag_name in existing_tags

                    # Desired propagation settings
                    desired_settings = {
                        "propagate": True,
                        "remove_propagation_on_delete": True,
                        "restrict_lineage_propagation": True,
                        "restrict_propagation_through_hierarchy": False,
                    }

                    if tag_exists:
                        try:
                            # Get current tag properties
                            current_tag = next(
                                tag
                                for tag in asset.atlan_tags
                                if tag.type_name == tag_name
                            )
                            current_settings = {
                                "propagate": current_tag.propagate,
                                "remove_propagation_on_delete": current_tag.remove_propagation_on_delete,
                                "restrict_lineage_propagation": current_tag.restrict_lineage_propagation,
                                "restrict_propagation_through_hierarchy": current_tag.restrict_propagation_through_hierarchy,
                            }

                            # Compare settings
                            if current_settings == desired_settings:
                                skipped_tags.append(tag_name)
                                continue

                            # Settings don't match, remove and re-add
                            atlan_client.asset.remove_atlan_tag(
                                guid=asset_guid, atlan_tag_name=tag_name
                            )
                            atlan_client.asset.add_atlan_tags(
                                asset_type=type(asset),
                                qualified_name=asset.qualified_name,
                                atlan_tag_names=[tag_name],
                                **desired_settings,
                            )
                            updated_tags.append(tag_name)
                        except Exception as e:
                            error_msg = f"Failed to update tag {tag_name}: {str(e)}"
                            failed_tags.append({"tag": tag_name, "error": str(e)})
                    else:
                        # Tag doesn't exist, add it with desired settings
                        try:
                            atlan_client.asset.add_atlan_tags(
                                asset_type=type(asset),
                                qualified_name=asset.qualified_name,
                                atlan_tag_names=[tag_name],
                                **desired_settings,
                            )
                            updated_tags.append(tag_name)
                        except Exception as e:
                            error_msg = f"Failed to add tag {tag_name}: {str(e)}"
                            failed_tags.append({"tag": tag_name, "error": str(e)})

                except Exception as e:
                    error_msg = f"Failed to process tag {tag_name}: {str(e)}"
                    failed_tags.append({"tag": tag_name, "error": str(e)})

            # Determine overall status for this asset
            if len(failed_tags) == len(tag_names):
                status = "error"
                message = "All tag operations failed"
            elif len(failed_tags) > 0:
                status = "partial_success"
                message = f"Some tag operations failed: {len(failed_tags)} failed, {len(updated_tags)} updated, {len(skipped_tags)} skipped"
            else:
                status = "success"
                message = f"All tag operations completed: {len(updated_tags)} updated, {len(skipped_tags)} skipped"

            # Store results for this asset
            results[asset_guid] = {
                "status": status,
                "message": message,
                "updated_tags": updated_tags,
                "skipped_tags": skipped_tags,
                "failed_tags": failed_tags,
            }

        except Exception as e:
            error_msg = f"Failed to process asset {asset_guid}: {str(e)}"
            logger.error(error_msg)
            results[asset_guid] = {
                "status": "error",
                "message": error_msg,
                "error": str(e),
                "error_type": "AssetProcessingError",
            }

    return results

import logging
from typing import Type, List, Optional, Union, Dict, Any

from client import get_atlan_client
from pyatlan.model.assets import Asset, AtlasGlossaryTerm
from pyatlan.model.fluent_search import CompoundQuery, FluentSearch
from pyatlan.model.fields.atlan_fields import AtlanField
from utils.search import SearchUtils
from utils.constants import DEFAULT_SEARCH_ATTRIBUTES

# Configure logging
logger = logging.getLogger(__name__)


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
) -> Dict[str, Any]:
    """
    Advanced asset search using FluentSearch with flexible conditions.

    By default, only essential attributes used in result processing are included.
    Additional attributes can be specified via include_attributes parameter.

    Args:
        conditions (Dict[str, Any], optional): Dictionary of attribute conditions to match.
            Format: {"attribute_name": value} or {"attribute_name": {"operator": operator, "value": value}}
        negative_conditions (Dict[str, Any], optional): Dictionary of attribute conditions to exclude.
            Format: {"attribute_name": value} or {"attribute_name": {"operator": operator, "value": value}}
        some_conditions (Dict[str, Any], optional): Conditions for where_some() queries that require min_somes of them to match.
            Format: {"attribute_name": value} or {"attribute_name": {"operator": operator, "value": value}}
        min_somes (int): Minimum number of some_conditions that must match. Defaults to 1.
        include_attributes (List[Union[str, AtlanField]], optional): List of additional attributes to include in results.
            Can be string attribute names or AtlanField objects. These will be added to the default set.
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
        Dict[str, Any]: Dictionary containing:
            - results: List of assets matching the search criteria
            - aggregations: Search aggregations if available
            - error: None if no error occurred, otherwise the error message
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
            if not isinstance(conditions, dict):
                error_msg = f"Conditions parameter must be a dictionary, got {type(conditions).__name__}"
                logger.error(error_msg)
                return []

            logger.debug(f"Applying positive conditions: {conditions}")
            for attr_name, condition in conditions.items():
                attr = SearchUtils._get_asset_attribute(attr_name)
                if attr is None:
                    logger.warning(
                        f"Unknown attribute: {attr_name}, skipping condition"
                    )
                    continue

                logger.debug(f"Processing condition for attribute: {attr_name}")

                search = SearchUtils._process_condition(
                    search, attr, condition, attr_name, "where"
                )

        # Apply negative conditions
        if negative_conditions:
            logger.debug(f"Applying negative conditions: {negative_conditions}")
            for attr_name, condition in negative_conditions.items():
                attr = SearchUtils._get_asset_attribute(attr_name)
                if attr is None:
                    logger.warning(
                        f"Unknown attribute for negative condition: {attr_name}, skipping"
                    )
                    continue

                logger.debug(
                    f"Processing negative condition for attribute: {attr_name}"
                )

                search = SearchUtils._process_condition(
                    search, attr, condition, attr_name, "where_not"
                )

        # Apply where_some conditions with min_somes
        if some_conditions:
            logger.debug(
                f"Applying 'some' conditions: {some_conditions} with min_somes={min_somes}"
            )
            for attr_name, condition in some_conditions.items():
                attr = SearchUtils._get_asset_attribute(attr_name)
                if attr is None:
                    logger.warning(
                        f"Unknown attribute for 'some' condition: {attr_name}, skipping"
                    )
                    continue

                logger.debug(f"Processing 'some' condition for attribute: {attr_name}")

                search = SearchUtils._process_condition(
                    search, attr, condition, attr_name, "where_some"
                )
            search = search.min_somes(min_somes)

        # Apply date range filters
        if date_range:
            logger.debug(f"Applying date range filters: {date_range}")
            date_range_count = 0
            for attr_name, range_cond in date_range.items():
                attr = SearchUtils._get_asset_attribute(attr_name)
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

        if guids and len(guids) > 0:
            logger.debug(f"Applying GUID filter: {guids}")
            search = search.where(Asset.GUID.within(guids))

        # Prepare attributes to include: default attributes + additional user-specified attributes
        all_attributes = DEFAULT_SEARCH_ATTRIBUTES.copy()

        if include_attributes:
            logger.debug(f"Adding user-specified attributes: {include_attributes}")
            for attr in include_attributes:
                if isinstance(attr, str):
                    if attr not in all_attributes:
                        all_attributes.append(attr)
                else:
                    # For AtlanField objects, we'll add them directly to the search
                    # They can't be easily compared for duplicates
                    pass

        logger.debug(f"Total attributes to include: {all_attributes}")

        # Include all attributes in results
        for attr_name in all_attributes:
            attr_obj = SearchUtils._get_asset_attribute(attr_name)
            if attr_obj is None:
                logger.warning(
                    f"Unknown attribute for inclusion: {attr_name}, skipping"
                )
                continue
            logger.debug(f"Including attribute: {attr_name}")
            search = search.include_on_results(attr_obj)

        # Include additional AtlanField objects specified by user
        if include_attributes:
            for attr in include_attributes:
                if not isinstance(attr, str):
                    # Assume it's already an AtlanField object
                    logger.debug(f"Including attribute object: {attr}")
                    search = search.include_on_results(attr)
        try:
            search = search.include_on_results(Asset.ASSIGNED_TERMS)
            search = search.include_on_relations(AtlasGlossaryTerm.NAME)
        except Exception as e:
            logger.warning(f"Error including assigned terms: {e}")

        # Set pagination
        logger.debug(f"Setting pagination: limit={limit}, offset={offset}")
        search = search.page_size(limit)
        if offset > 0:
            search = search.from_offset(offset)

        # Set sorting
        if sort_by:
            sort_attr = SearchUtils._get_asset_attribute(sort_by)
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

        logger.info("Executing search request")
        client = get_atlan_client()
        search_response = client.asset.search(request)
        processed_results = SearchUtils.process_results(search_response)
        logger.info(
            f"Search completed, returned {len(processed_results['results'])} results"
        )
        return processed_results

    except Exception as e:
        logger.error(f"Error searching assets: {str(e)}")
        return [{"results": [], "aggregations": {}, "error": str(e)}]

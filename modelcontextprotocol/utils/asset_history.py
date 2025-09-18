"""
Utility functions for asset history operations.

This module contains helper functions for retrieving and processing asset audit history.
"""

import logging
from typing import List, Union, Dict, Any, Optional
from pyatlan.client.audit import AuditSearchRequest
from pyatlan.model.search import DSL, Bool, SortItem, Term
from pyatlan.model.enums import SortOrder
from pyatlan.model.fields.atlan_fields import AtlanField

# Initialize logging
logger = logging.getLogger(__name__)

def validate_asset_history_params(
    guid: Optional[str],
    qualified_name: Optional[str],
    type_name: Optional[str],
    sort_order: str,
) -> Optional[str]:
    """
    Validate input parameters for asset history retrieval.

    Args:
        guid: Asset GUID
        qualified_name: Asset qualified name
        type_name: Asset type name
        sort_order: Sort order

    Returns:
        Error message if validation fails, None if valid
    """
    if not guid and not qualified_name:
        return "Either guid or qualified_name must be provided"

    if qualified_name and not type_name:
        return "type_name is required when using qualified_name"

    if sort_order not in ["ASC", "DESC"]:
        return "sort_order must be either 'ASC' or 'DESC'"

    return None


def create_audit_search_request(
    guid: Optional[str],
    qualified_name: Optional[str],
    type_name: Optional[str],
    size: int,
    sort_item: SortItem
) -> AuditSearchRequest:
    """
    Create an AuditSearchRequest based on the provided parameters.

    Args:
        guid: Asset GUID
        qualified_name: Asset qualified name
        type_name: Asset type name
        size: Number of results to return
        sort_item: Sort configuration

    Returns:
        Configured AuditSearchRequest
    """
    if guid:
        dsl = DSL(
            query=Bool(filter=[Term(field="entityId", value=guid)]),
            sort=[sort_item],
            size=size,
        )
        logger.debug(f"Created audit search request by GUID: {guid}")
    else:
        dsl = DSL(
            query=Bool(
                must=[
                    Term(field="entityQualifiedName", value=qualified_name),
                    Term(field="typeName", value=type_name),
                ]
            ),
            sort=[sort_item],
            size=size,
        )
        logger.debug(
            f"Created audit search request by qualified name: {qualified_name}"
        )

    return AuditSearchRequest(dsl=dsl)


def extract_basic_audit_info(result) -> Dict[str, Any]:
    """
    Extract basic audit information from a result object.

    Args:
        result: Audit result object

    Returns:
        Dictionary with basic audit information
    """
    return {
        "entityQualifiedName": getattr(result, "entity_qualified_name", None),
        "guid": getattr(result, "entity_id", None),
        "typeName": getattr(result, "type_name", None),
        "timestamp": getattr(result, "timestamp", None),
        "action": getattr(result, "action", None),
        "user": getattr(result, "user", None),
        "created": getattr(result, "created", None),
    }


def process_audit_result(
    result
) -> Dict[str, Any]:
    """
    Process a single audit result into a formatted dictionary.

    Args:
        result: Audit result object

    Returns:
        Formatted audit entry dictionary
    """
    try:
        # Extract basic audit information
        audit_entry = extract_basic_audit_info(result)
        updates = result.detail.dict(
            exclude_unset=True
        )
        audit_entry.update(updates)

        return audit_entry

    except Exception as e:
        logger.warning(f"Error processing audit result: {e}")
        return {
            "error": f"Failed to process audit entry: {str(e)}",
            "entityQualifiedName": "Unknown",
            "guid": "Unknown",
        }


def create_sort_item(sort_order: str) -> SortItem:
    """
    Create a SortItem based on the sort order.

    Args:
        sort_order: Sort order ("ASC" or "DESC")

    Returns:
        Configured SortItem
    """
    return SortItem(
        "created",
        order=SortOrder.DESCENDING if sort_order == "DESC" else SortOrder.ASCENDING,
    )

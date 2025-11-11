"""
Utility functions for asset history operations.

This module contains helper functions for retrieving and processing asset audit history.
"""

import logging
from typing import Optional
from pyatlan.client.audit import AuditSearchRequest
from pyatlan.model.search import DSL, Bool, SortItem, Term
from pyatlan.model.enums import SortOrder

# Initialize logging
logger = logging.getLogger(__name__)


def create_audit_search_request(
    guid: Optional[str],
    qualified_name: Optional[str],
    type_name: Optional[str],
    size: int,
    sort_order: str,
) -> AuditSearchRequest:
    """
    Create an AuditSearchRequest based on the provided parameters.

    Args:
        guid: Asset GUID
        qualified_name: Asset qualified name
        type_name: Asset type name
        size: Number of results to return
        sort_order: Sort order ("ASC" or "DESC")

    Returns:
        Configured AuditSearchRequest
    """
    # Create sort item inline
    sort_item = SortItem(
        "created",
        order=SortOrder.DESCENDING if sort_order == "DESC" else SortOrder.ASCENDING,
    )

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


def process_audit_result(result):
    """
    Process a single audit result into AuditEntry data.

    Args:
        result: Audit result object

    Returns:
        Dictionary with audit entry data for AuditEntry model
    """
    # Import here to avoid circular dependency
    from tools.models import AuditEntry

    # Extract basic audit information
    audit_data = {
        "guid": getattr(result, "entity_id", None),
        "timestamp": getattr(result, "timestamp", None),
        "action": getattr(result, "action", None),
        "user": getattr(result, "user", None),
    }

    # Add detail updates as additional fields
    detail_updates = result.detail.dict(exclude_unset=True)
    audit_data.update(detail_updates)

    return AuditEntry(**audit_data)

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SearchUtils:
    @staticmethod
    def process_results(
        results: Any, include_attributes: Optional[List[str]] = None
    ) -> tuple[List[Dict[str, Any]], Any, int]:
        """
        Process the results from the search index safely.

        Args:
            results: The search results from Atlan
            include_attributes: Additional attributes to include in the output
        """
        results_list = []
        aggregations = getattr(results, "aggregations", None)
        count = getattr(results, "count", 0)
        current_page_results = (
            results.current_page()
            if hasattr(results, "current_page") and callable(results.current_page)
            else []
        )

        for result in current_page_results:
            # Add check to skip processing if result is None or has no attributes
            if result is None or not hasattr(result, "attributes"):
                continue

            # Convert set to list for owner_users and handle None case safely
            owner_users = []
            raw_owner_users = getattr(result.attributes, "owner_users", None)
            if raw_owner_users:
                owner_users = (
                    list(raw_owner_users)
                    if isinstance(raw_owner_users, set)
                    else raw_owner_users
                )

            # Convert datetime objects to ISO format strings safely
            def safe_isoformat(dt):
                return dt.isoformat() if isinstance(dt, datetime) else None

            source_created_at = safe_isoformat(
                getattr(result.attributes, "source_created_at", None)
            )
            source_updated_at = safe_isoformat(
                getattr(result.attributes, "source_updated_at", None)
            )
            last_sync_run_at = safe_isoformat(
                getattr(result.attributes, "last_sync_run_at", None)
            )

            # Convert AtlanTag objects to dictionaries safely
            atlan_tags = []
            raw_atlan_tags = getattr(result, "atlan_tags", None)
            if raw_atlan_tags:
                for tag in raw_atlan_tags:
                    if tag is None:
                        continue
                    tag_dict = {
                        "type_name": str(getattr(tag, "type_name", None)),
                        "entity_guid": getattr(tag, "entity_guid", None),
                        "entity_status": str(getattr(tag.entity_status, "value", None))
                        if getattr(tag, "entity_status", None)
                        else None,
                    }
                    atlan_tags.append(tag_dict)

            # Extract glossary terms safely
            glossary_terms = list(getattr(result, "meaning_names", None) or [])

            # Extract readme safely
            readme_description = None
            readme_attr = getattr(result.attributes, "readme", None)
            if (
                readme_attr
                and hasattr(readme_attr, "attributes")
                and hasattr(readme_attr.attributes, "description")
            ):
                readme_description = readme_attr.attributes.description

            # Safely get certificate status string
            cert_status_enum = getattr(result.attributes, "certificate_status", None)
            certificate_status_str = str(cert_status_enum) if cert_status_enum else None

            # Base result dictionary with core attributes
            # this is directly linked to the MessageArtifact model in the db, make sure to update it when the model changes
            result_dict = {
                "type": getattr(result, "type_name", None),
                "name": getattr(result.attributes, "name", None),
                "display_name": getattr(result.attributes, "display_name", None),
                "description": getattr(result.attributes, "description", None),
                "guid": getattr(result, "guid", None),
                "qualified_name": getattr(result.attributes, "qualified_name", None),
                "user_description": getattr(
                    result.attributes, "user_description", None
                ),
                "tenant_id": getattr(result.attributes, "tenant_id", None),
                "certificate_status": certificate_status_str,
                "owner_users": owner_users,
                "connector_name": getattr(result.attributes, "connector_name", None),
                "has_lineage": getattr(result.attributes, "has_lineage", None),
                "source_created_at": source_created_at,
                "source_updated_at": source_updated_at,
                "last_sync_run_at": last_sync_run_at,
                "atlan_tags": atlan_tags,
                "glossary_terms": glossary_terms,
                "readme": readme_description,
            }

            # Add any additional attributes requested by the user
            if include_attributes:
                for attr_name in include_attributes:
                    # Skip if already included in base result_dict
                    if attr_name.lower() in [key.lower() for key in result_dict.keys()]:
                        continue

                    # Get the attribute value from the result
                    attr_value = getattr(result.attributes, attr_name.lower(), None)

                    # Handle special cases for complex attribute types
                    if attr_value is not None:
                        # Convert sets to lists for JSON serialization
                        if isinstance(attr_value, set):
                            attr_value = list(attr_value)
                        # Convert datetime objects to ISO format
                        elif isinstance(attr_value, datetime):
                            attr_value = attr_value.isoformat()
                        # Handle enum types by converting to string
                        elif hasattr(attr_value, "value"):
                            attr_value = str(attr_value)
                        # Handle complex objects that might have a string representation
                        elif hasattr(attr_value, "__dict__") and not isinstance(
                            attr_value, (str, int, float, bool)
                        ):
                            # For complex objects, try to extract meaningful data
                            try:
                                attr_value = str(attr_value)
                            except Exception as e:
                                logger.error(
                                    f"Error processing attribute {attr_name}: {e}"
                                )
                                attr_value = None

                    result_dict[attr_name] = attr_value

            results_list.append(result_dict)
        return results_list, aggregations, count

"""Utility functions for glossary operations."""

import logging
from typing import Any, Dict, List, Optional, Union, TypeVar, Callable
from client import get_atlan_client
from . import parse_list_parameter
from pyatlan.model.assets import Asset
from tools.models import CertificateStatus

logger = logging.getLogger(__name__)

# Type variables for generic functions
T = TypeVar("T")
SpecType = TypeVar("SpecType")


def process_certificate_status(
    asset: Asset, certificate_status: Optional[Union[str, CertificateStatus]]
) -> None:
    """
    Process and set certificate status on an asset.

    Args:
        asset: The asset to set certificate status on
        certificate_status: Certificate status to set (string or enum)
    """
    if certificate_status is not None:
        if isinstance(certificate_status, str):
            certificate_status = CertificateStatus(certificate_status)
        asset.certificate_status = certificate_status.value


def process_owners(
    asset: Asset,
    owner_users: Optional[List[str]] = None,
    owner_groups: Optional[List[str]] = None,
) -> None:
    """
    Process and set owners on an asset.

    Args:
        asset: The asset to set owners on
        owner_users: List of user names
        owner_groups: List of group names
    """
    normalised_owner_users = parse_list_parameter(owner_users)
    if normalised_owner_users:
        asset.owner_users = set(normalised_owner_users)

    normalised_owner_groups = parse_list_parameter(owner_groups)
    if normalised_owner_groups:
        asset.owner_groups = set(normalised_owner_groups)


def extract_guid_from_response(response) -> Optional[str]:
    """
    Extract GUID from Atlan API response.

    Args:
        response: Response from Atlan API

    Returns:
        GUID string if found, None otherwise
    """
    if response and response.guid_assignments:
        return list(response.guid_assignments.values())[0]
    return None


def create_success_result(
    guid: Optional[str],
    name: str,
    qualified_name: str,
    extra_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a success result dictionary.

    Args:
        guid: Asset GUID
        name: Asset name
        qualified_name: Asset qualified name
        extra_fields: Additional fields to include

    Returns:
        Success result dictionary
    """
    result = {
        "guid": guid,
        "name": name,
        "qualified_name": qualified_name,
        "success": True,
        "errors": [],
    }

    if extra_fields:
        result.update(extra_fields)

    return result


def create_error_result(
    name: str,
    error_msg: str,
    extra_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create an error result dictionary.

    Args:
        name: Asset name
        error_msg: Error message
        extra_fields: Additional fields to include

    Returns:
        Error result dictionary
    """
    result = {
        "guid": None,
        "name": name,
        "qualified_name": None,
        "success": False,
        "errors": [error_msg],
    }

    if extra_fields:
        result.update(extra_fields)

    return result


def validate_required_fields(
    spec_dict: Dict[str, Any], required_fields: List[str], index: int, item_type: str
) -> Optional[str]:
    """
    Validate that required fields are present in specification.

    Args:
        spec_dict: Specification dictionary
        required_fields: List of required field names
        index: Index of item being processed
        item_type: Type of item (for error messages)

    Returns:
        Error message if validation fails, None if valid
    """
    for field in required_fields:
        if field not in spec_dict:
            return f"{item_type} at index {index}: '{field}' field is required"
    return None


def create_batch_processor(
    single_creation_func: Callable,
    spec_class: type,
    required_fields: List[str],
    item_type: str,
) -> Callable:
    """
    Create a generic batch processor function.

    Args:
        single_creation_func: Function to create single item
        spec_class: Specification class for validation
        required_fields: List of required fields for validation
        item_type: Type name for logging/errors

    Returns:
        Batch processing function
    """

    def batch_processor(
        items: Union[Dict[str, Any], object, List[Union[Dict[str, Any], object]]],
    ) -> Dict[str, Any]:
        # Normalize input to always be a list for consistent processing
        if isinstance(items, (dict, spec_class)):
            item_list = [items]
            is_batch = False
            logger.info(f"Creating single {item_type} asset")
        else:
            item_list = items
            is_batch = True
            logger.info(f"Creating {len(item_list)} {item_type}s in batch")

        if not item_list:
            return {
                "results": [],
                "successful_count": 0,
                "failed_count": 0,
                "overall_success": True,
                "errors": [f"No {item_type}s provided for creation"],
                "is_batch": is_batch,
            }

        results = []
        successful_count = 0
        failed_count = 0
        overall_errors = []

        try:
            # Process each item specification
            for i, item_spec in enumerate(item_list):
                try:
                    # Convert dict to specification class if needed
                    if isinstance(item_spec, dict):
                        # Validate required fields
                        error_msg = validate_required_fields(
                            item_spec, required_fields, i, item_type.capitalize()
                        )
                        if error_msg:
                            logger.error(error_msg)
                            error_result = {
                                "index": i,
                                "name": item_spec.get("name"),
                                "guid": None,
                                "qualified_name": None,
                                "success": False,
                                "errors": [error_msg],
                            }
                            # Add extra fields specific to item type
                            if "glossary_guid" in item_spec:
                                error_result["glossary_guid"] = item_spec.get(
                                    "glossary_guid"
                                )
                            results.append(error_result)
                            failed_count += 1
                            continue

                        spec = spec_class(**item_spec)
                    else:
                        spec = item_spec

                    # Create individual item using the provided function
                    result = single_creation_func(spec)

                    # Add index to result for tracking
                    result["index"] = i
                    results.append(result)

                    if result["success"]:
                        successful_count += 1
                        logger.info(
                            f"Successfully created {item_type} '{spec.name}' at index {i}"
                        )
                    else:
                        failed_count += 1
                        logger.error(
                            f"Failed to create {item_type} '{spec.name}' at index {i}: {result.get('errors', [])}"
                        )

                except Exception as e:
                    error_msg = f"Error processing {item_type} at index {i}: {str(e)}"
                    logger.error(error_msg)
                    logger.exception("Exception details:")

                    error_result = {
                        "index": i,
                        "name": item_spec.get("name")
                        if isinstance(item_spec, dict)
                        else getattr(item_spec, "name", None),
                        "guid": None,
                        "qualified_name": None,
                        "success": False,
                        "errors": [error_msg],
                    }
                    # Add extra fields specific to item type
                    if hasattr(item_spec, "glossary_guid") or (
                        isinstance(item_spec, dict) and "glossary_guid" in item_spec
                    ):
                        error_result["glossary_guid"] = (
                            item_spec.get("glossary_guid")
                            if isinstance(item_spec, dict)
                            else getattr(item_spec, "glossary_guid", None)
                        )
                    results.append(error_result)
                    failed_count += 1

        except Exception as e:
            error_msg = f"Critical error during {item_type} creation: {str(e)}"
            logger.error(error_msg)
            logger.exception("Exception details:")
            overall_errors.append(error_msg)

        overall_success = failed_count == 0 and len(overall_errors) == 0

        summary = {
            "results": results,
            "successful_count": successful_count,
            "failed_count": failed_count,
            "overall_success": overall_success,
            "errors": overall_errors,
            "is_batch": is_batch,
        }

        operation_type = "batch" if is_batch else "single"
        logger.info(
            f"{operation_type.capitalize()} {item_type} creation completed: {successful_count} successful, {failed_count} failed"
        )
        return summary

    return batch_processor


def create_asset_with_error_handling(
    asset_creator: Callable[[], Asset],
    asset_name: str,
    asset_type: str,
    extra_result_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generic function to create an asset with consistent error handling.

    Args:
        asset_creator: Function that creates and returns the asset
        asset_name: Name of the asset being created
        asset_type: Type of asset (for logging)
        extra_result_fields: Additional fields to include in result

    Returns:
        Result dictionary with success/error information
    """
    logger.info(f"Creating {asset_type}: {asset_name}")

    try:
        # Create the asset
        asset = asset_creator()

        # Get Atlan client and save the asset
        client = get_atlan_client()
        response = client.asset.save(asset)

        # Extract GUID from response
        created_guid = extract_guid_from_response(response)

        # Create success result
        result = create_success_result(
            guid=created_guid,
            name=asset_name,
            qualified_name=asset.qualified_name,
            extra_fields=extra_result_fields,
        )

        logger.info(
            f"Successfully created {asset_type}: {asset_name} with GUID: {created_guid}"
        )
        return result

    except Exception as e:
        error_msg = f"Error creating {asset_type} '{asset_name}': {str(e)}"
        logger.error(error_msg)
        return create_error_result(
            name=asset_name,
            error_msg=error_msg,
            extra_fields=extra_result_fields,
        )

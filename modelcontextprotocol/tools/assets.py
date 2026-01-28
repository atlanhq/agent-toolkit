import logging
from typing import List, Union, Dict, Any
from client import get_atlan_client
from .models import (
    UpdatableAsset,
    UpdatableAttribute,
    CertificateStatus,
    TermOperation,
    TermOperations,
    AtlanTagOperations,
    OwnerOperations,
)
from pyatlan.model.assets import Readme, AtlasGlossaryTerm, AtlasGlossaryCategory
from pyatlan.model.fluent_search import CompoundQuery, FluentSearch
from pyatlan.cache.atlan_tag_cache import AtlanTagCache

# Initialize logging
logger = logging.getLogger(__name__)


def _validate_atlan_tags(client, tag_names: List[str]) -> List[str]:
    """
    Validate that Atlan tags exist using cache.

    Args:
        client: Atlan client instance
        tag_names: List of tag names to validate

    Returns:
        List of invalid tag names (empty if all valid)

    Raises:
        Exception: If there's an error accessing the tag cache
    """
    invalid_tags = []

    for tag_name in tag_names:
        try:
            # Use cache to check if tag exists
            # get_id_for_name will return None if tag doesn't exist
            tag_id = AtlanTagCache.get_id_for_name(client=client, name=tag_name)
            if not tag_id:
                invalid_tags.append(tag_name)
        except Exception as e:
            logger.warning(f"Error validating tag '{tag_name}': {str(e)}")
            invalid_tags.append(tag_name)

    return invalid_tags


def _validate_owners(
    client, owner_usernames: List[str], owner_type: str
) -> List[str]:
    """
    Validate that owner users or groups exist in Atlan using direct API calls.

    Args:
        client: Atlan client instance
        owner_usernames: List of usernames or group names
        owner_type: "owner_users" or "owner_groups"

    Returns:
        List of invalid owner usernames (empty if all valid)

    Raises:
        Exception: If there's an error accessing user/group APIs
    """
    invalid_owners = []

    for username in owner_usernames:
        try:
            if owner_type == "owner_users":
                # Validate username only (exact match)
                user = client.user.get_by_username(username)
                if not user:
                    invalid_owners.append(username)
                    logger.info(f"User '{username}' not found")
                else:
                    logger.info(f"User '{username}' validated")
            else:  # owner_groups
                # Validate group name - NOTE: get_by_name does CONTAINS search, not exact match
                groups = client.group.get_by_name(username)

                # Check for EXACT group name match in the returned records
                exact_match_found = False
                if groups and groups.records:
                    for g in groups.records:
                        if g.alias and g.alias.lower() == username.lower():
                            exact_match_found = True
                            break

                if not exact_match_found:
                    invalid_owners.append(username)
                    logger.info(f"Group '{username}' not found (no exact match)")
                else:
                    logger.info(f"Group '{username}' validated (exact match)")
        except Exception as e:
            logger.warning(f"Error validating owner '{username}': {str(e)}")
            invalid_owners.append(username)

    return invalid_owners


def _update_owners(
    client,
    asset_cls,
    asset,
    qualified_name: str,
    operation: TermOperation,
    owner_values: List[str],
    owner_type: str,  # "owner_users" or "owner_groups"
) -> None:
    """
    Helper to handle owner operations for both users and groups.

    Args:
        client: Atlan client instance
        asset_cls: Asset class type
        asset: Asset updater instance to modify
        qualified_name: Qualified name of the asset
        operation: Operation to perform (append, replace, remove)
        owner_values: List of usernames/emails or group names
        owner_type: Either "owner_users" or "owner_groups"
    """
    if operation == TermOperation.REPLACE:
        setattr(asset, owner_type, owner_values)
        return

    # For append/remove, fetch current owners
    include_field = (
        asset_cls.OWNER_USERS if owner_type == "owner_users" else asset_cls.OWNER_GROUPS
    )

    asset_response = (
        FluentSearch()
        .select()
        .where(CompoundQuery.asset_type(asset_cls))
        .where(asset_cls.QUALIFIED_NAME.eq(qualified_name))
        .include_on_results(include_field)
        .execute(client=client)
    )

    current_owners = []
    if first := asset_response.current_page():
        current_owners = getattr(first[0], owner_type) or []

    if operation == TermOperation.APPEND:
        combined_owners = list(set(current_owners + owner_values))
        setattr(asset, owner_type, combined_owners)
    elif operation == TermOperation.REMOVE:
        remaining_owners = [o for o in current_owners if o not in owner_values]
        setattr(asset, owner_type, remaining_owners)


def update_assets(
    updatable_assets: Union[UpdatableAsset, List[UpdatableAsset]],
    attribute_name: UpdatableAttribute,
    attribute_values: List[
        Union[str, CertificateStatus, TermOperations, AtlanTagOperations, OwnerOperations]
    ],
) -> Dict[str, Any]:
    """
    Update one or multiple assets with different values for attributes or operations.

    Args:
        updatable_assets (Union[UpdatableAsset, List[UpdatableAsset]]): Asset(s) to update.
            Can be a single UpdatableAsset or a list of UpdatableAssets.
            For asset of type_name=AtlasGlossaryTerm or type_name=AtlasGlossaryCategory, each asset dictionary MUST include a "glossary_guid" key which is the GUID of the glossary that the term belongs to.
        attribute_name (UpdatableAttribute): Name of the attribute to update.
            Supports userDescription, certificateStatus, readme, term, atlan_tags, owner_users, and owner_groups.
        attribute_values (List[Union[str, CertificateStatus, TermOperations, AtlanTagOperations, OwnerOperations]]): List of values to set for the attribute.
            For certificateStatus, only VERIFIED, DRAFT, or DEPRECATED are allowed.
            For readme, the value must be a valid Markdown string.
            For term, the value must be a TermOperations object with operation and term_guids.
            For atlan_tags, the value must be an AtlanTagOperations object with operation and atlan_tag_names.
            For owner_users/owner_groups, the value must be an OwnerOperations object with operation and owner_usernames.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - updated_count: Number of assets successfully updated
            - errors: List of any errors encountered
    """
    try:
        # Convert single asset to list for consistent handling
        if not isinstance(updatable_assets, list):
            updatable_assets = [updatable_assets]

        logger.info(
            f"Updating {len(updatable_assets)} assets with attribute '{attribute_name}'"
        )

        # Validate attribute values
        if len(updatable_assets) != len(attribute_values):
            error_msg = "Number of asset GUIDs must match number of attribute values"
            logger.error(error_msg)
            return {"updated_count": 0, "errors": [error_msg]}

        # Initialize result tracking
        result = {"updated_count": 0, "errors": []}

        # Validate certificate status values if applicable
        if attribute_name == UpdatableAttribute.CERTIFICATE_STATUS:
            for value in attribute_values:
                if value not in CertificateStatus.__members__.values():
                    error_msg = f"Invalid certificate status: {value}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)

        # Get Atlan client
        client = get_atlan_client()

        # Create assets with updated values
        assets = []
        # readme_update_parent_assets: Assets that were updated with readme.
        readme_update_parent_assets = []
        for index, updatable_asset in enumerate(updatable_assets):
            type_name = updatable_asset.type_name
            qualified_name = updatable_asset.qualified_name
            asset_cls = getattr(
                __import__("pyatlan.model.assets", fromlist=[type_name]), type_name
            )

            # Special handling for Glossary Term updates
            if (
                updatable_asset.type_name == AtlasGlossaryTerm.__name__
                or updatable_asset.type_name == AtlasGlossaryCategory.__name__
            ):
                asset = asset_cls.updater(
                    qualified_name=updatable_asset.qualified_name,
                    name=updatable_asset.name,
                    glossary_guid=updatable_asset.glossary_guid,
                )
            else:
                asset = asset_cls.updater(
                    qualified_name=updatable_asset.qualified_name,
                    name=updatable_asset.name,
                )

            # Special handling for README updates
            if attribute_name == UpdatableAttribute.README:
                # Get the current readme content for the asset
                # The below query is used to get the asset based on the qualified name and include the readme content.
                asset_readme_response = (
                    FluentSearch()
                    .select()
                    .where(CompoundQuery.asset_type(asset_cls))
                    .where(asset_cls.QUALIFIED_NAME.eq(qualified_name))
                    .include_on_results(asset_cls.README)
                    .include_on_relations(Readme.DESCRIPTION)
                    .execute(client=client)
                )

                if first := asset_readme_response.current_page():
                    updated_content = attribute_values[index]
                    # We replace the existing readme content with the new content.
                    # If the existing readme content is not present, we create a new readme asset.
                    updated_readme = Readme.creator(
                        asset=first[0], content=updated_content
                    )
                    # Save the readme asset
                    assets.append(updated_readme)
                    # Add the parent/actual asset to the list of assets that were updated with readme.
                    readme_update_parent_assets.append(asset)
            elif attribute_name == UpdatableAttribute.TERM:
                # Special handling for term operations
                term_value = attribute_values[index]
                if not isinstance(term_value, TermOperations):
                    error_msg = f"Term value must be a TermOperations object for asset {updatable_asset.qualified_name}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    continue

                term_operation = TermOperation(term_value.operation.lower())
                term_guids = term_value.term_guids

                # Create term references
                term_refs = [
                    AtlasGlossaryTerm.ref_by_guid(guid=guid) for guid in term_guids
                ]

                try:
                    # Perform the appropriate term operation
                    if term_operation == TermOperation.APPEND:
                        client.asset.append_terms(
                            asset_type=asset_cls,
                            qualified_name=updatable_asset.qualified_name,
                            terms=term_refs,
                        )
                    elif term_operation == TermOperation.REPLACE:
                        client.asset.replace_terms(
                            asset_type=asset_cls,
                            qualified_name=updatable_asset.qualified_name,
                            terms=term_refs,
                        )
                    elif term_operation == TermOperation.REMOVE:
                        client.asset.remove_terms(
                            asset_type=asset_cls,
                            qualified_name=updatable_asset.qualified_name,
                            terms=term_refs,
                        )

                    result["updated_count"] += 1
                    logger.info(
                        f"Successfully {term_operation.value}d terms on asset: {updatable_asset.qualified_name}"
                    )

                except Exception as e:
                    error_msg = f"Error updating terms on asset {updatable_asset.qualified_name}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
            elif attribute_name == UpdatableAttribute.ATLAN_TAGS:
                # Atlan tags handling
                tag_value = attribute_values[index]
                if not isinstance(tag_value, AtlanTagOperations):
                    error_msg = f"Atlan tag value must be an AtlanTagOperations object for asset {updatable_asset.qualified_name}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    continue

                tag_operation = TermOperation(tag_value.operation.lower())
                tag_names = tag_value.atlan_tag_names

                # Validate tags exist before performing operations
                invalid_tags = _validate_atlan_tags(client, tag_names)
                if invalid_tags:
                    error_msg = f"Tags do not exist in Atlan: {', '.join(invalid_tags)}. Please create these tags before applying them to assets."
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    continue

                try:
                    if tag_operation == TermOperation.APPEND:
                        client.asset.add_atlan_tags(
                            asset_type=asset_cls,
                            qualified_name=updatable_asset.qualified_name,
                            atlan_tag_names=tag_names,
                        )
                    elif tag_operation == TermOperation.REPLACE:
                        client.asset.update_atlan_tags(
                            asset_type=asset_cls,
                            qualified_name=updatable_asset.qualified_name,
                            atlan_tag_names=tag_names,
                        )
                    elif tag_operation == TermOperation.REMOVE:
                        client.asset.remove_atlan_tags(
                            asset_type=asset_cls,
                            qualified_name=updatable_asset.qualified_name,
                            atlan_tag_names=tag_names,
                        )

                    result["updated_count"] += 1
                    logger.info(
                        f"Successfully {tag_operation.value}d atlan tags on asset: {updatable_asset.qualified_name}"
                    )

                except Exception as e:
                    error_msg = f"Error updating atlan tags on asset {updatable_asset.qualified_name}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
            elif attribute_name in [
                UpdatableAttribute.OWNER_USERS,
                UpdatableAttribute.OWNER_GROUPS,
            ]:
                # Owner handling (users or groups)
                owner_value = attribute_values[index]
                if not isinstance(owner_value, OwnerOperations):
                    error_msg = f"Owner value must be an OwnerOperations object for asset {updatable_asset.qualified_name}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    continue

                owner_operation = TermOperation(owner_value.operation.lower())
                owner_usernames = owner_value.owner_usernames
                owner_type = attribute_name.value  # "owner_users" or "owner_groups"

                # Validate owners exist before performing operations
                invalid_owners = _validate_owners(client, owner_usernames, owner_type)

                if invalid_owners:
                    entity_type = "users" if owner_type == "owner_users" else "groups"
                    error_msg = f"{entity_type.capitalize()} do not exist in Atlan: {', '.join(invalid_owners)}. Please provide exact {entity_type[:-1]} name as it appears in Atlan."
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    continue

                try:
                    _update_owners(
                        client=client,
                        asset_cls=asset_cls,
                        asset=asset,
                        qualified_name=updatable_asset.qualified_name,
                        operation=owner_operation,
                        owner_values=owner_usernames,
                        owner_type=owner_type,
                    )
                    assets.append(asset)

                except Exception as e:
                    error_msg = f"Error updating {owner_type} on asset {updatable_asset.qualified_name}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
            else:
                # Regular attribute update flow
                setattr(asset, attribute_name.value, attribute_values[index])
                assets.append(asset)

        if len(readme_update_parent_assets) > 0:
            result["readme_updated"] = len(readme_update_parent_assets)
            # Collect qualified names or other identifiers for assets that were updated with readme
            result["updated_readme_assets"] = [
                asset.qualified_name
                for asset in readme_update_parent_assets
                if hasattr(asset, "qualified_name")
            ]
            logger.info(
                f"Successfully updated {result['readme_updated']} readme assets: {result['updated_readme_assets']}"
            )

        # Proces response
        if len(assets) > 0:
            response = client.asset.save(assets)
            result["updated_count"] = len(response.guid_assignments)
        logger.info(f"Successfully updated {result['updated_count']} assets")

        return result

    except Exception as e:
        error_msg = f"Error updating assets: {str(e)}"
        logger.error(error_msg)
        return {"updated_count": 0, "errors": [error_msg]}

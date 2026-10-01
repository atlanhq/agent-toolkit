import logging
from typing import List, Union, Dict, Any
from client import get_atlan_client
from .models import (
    UpdatableAsset,
    UpdatableAttribute,
    CertificateStatus,
    TermOperation,
    TermOperations,
    TagOperation,
    TagOperations,
)
from pyatlan.model.assets import Readme, AtlasGlossaryTerm, AtlasGlossaryCategory
from pyatlan.model.fluent_search import CompoundQuery, FluentSearch

# Initialize logging
logger = logging.getLogger(__name__)


def update_assets(
    updatable_assets: Union[UpdatableAsset, List[UpdatableAsset]],
    attribute_name: UpdatableAttribute,
    attribute_values: List[Union[str, CertificateStatus, TermOperations, TagOperations]],
) -> Dict[str, Any]:
    """
    Update one or multiple assets with different values for attributes, term operations, or tag operations.

    Args:
        updatable_assets (Union[UpdatableAsset, List[UpdatableAsset]]): Asset(s) to update.
            Can be a single UpdatableAsset or a list of UpdatableAssets.
            For asset of type_name=AtlasGlossaryTerm or type_name=AtlasGlossaryCategory, each asset dictionary MUST include a "glossary_guid" key which is the GUID of the glossary that the term belongs to.
        attribute_name (UpdatableAttribute): Name of the attribute to update.
            Supports user_description, certificate_status, readme, term, and tag.
        attribute_values (List[Union[str, CertificateStatus, TermOperations, TagOperations]]): List of values to set for the attribute.
            For certificateStatus, only VERIFIED, DRAFT, or DEPRECATED are allowed.
            For readme, the value must be a valid Markdown string.
            For term, the value must be a TermOperations object with operation and term_guids.
            For tag, the value must be a TagOperations object with operation and tag_names.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - updated_count: Number of assets successfully updated
            - errors: List of any errors encountered
            - operation: The operation that was performed (for term/tag operations)
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
            elif attribute_name == UpdatableAttribute.TAG:
                # Special handling for tag operations
                tag_value = attribute_values[index]
                if isinstance(tag_value, dict):
                    try:
                        tag_value = TagOperations(**tag_value)
                    except Exception as e:
                        error_msg = f"Invalid tag operation dictionary for asset {updatable_asset.qualified_name}: {str(e)}"
                        logger.error(error_msg)
                        result["errors"].append(error_msg)
                        continue
                elif not isinstance(tag_value, TagOperations):
                    error_msg = f"Tag value must be a TagOperations object for asset {updatable_asset.qualified_name}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    continue

                tag_operation = TagOperation(tag_value.operation.value if isinstance(tag_value.operation, TagOperation) else str(tag_value.operation).lower())
                tag_names = tag_value.tag_names

                if not tag_names and tag_operation in (TagOperation.ADD, TagOperation.REMOVE):
                    error_msg = (
                        f"At least one tag name must be provided for '{tag_operation.value}' operation on asset {updatable_asset.qualified_name}."
                    )
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    continue

                # Validate that all specified tags exist in the system
                invalid_tags = []
                for name in tag_names:
                    try:
                        tag_id = client.atlan_tag_cache.get_id_for_name(name)
                        if not tag_id:
                            invalid_tags.append(name)
                    except Exception:
                        invalid_tags.append(name)

                if invalid_tags:
                    error_msg = (
                        f"The following tag(s) do not exist in the system: {', '.join(invalid_tags)}. "
                        f"Please ensure tags exist before applying them to asset {updatable_asset.qualified_name}."
                    )
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    continue

                try:
                    # Perform the appropriate tag operation
                    if tag_operation == TagOperation.ADD:
                        client.asset.add_atlan_tags(
                            asset_type=asset_cls,
                            qualified_name=updatable_asset.qualified_name,
                            atlan_tag_names=tag_names,
                            propagate=tag_value.propagate if tag_value.propagate is not None else False,
                            remove_propagation_on_delete=tag_value.remove_propagation_on_delete if tag_value.remove_propagation_on_delete is not None else True,
                            restrict_lineage_propagation=tag_value.restrict_lineage_propagation if tag_value.restrict_lineage_propagation is not None else False,
                            restrict_propagation_through_hierarchy=tag_value.restrict_propagation_through_hierarchy if tag_value.restrict_propagation_through_hierarchy is not None else False,
                        )
                    elif tag_operation == TagOperation.REMOVE:
                        client.asset.remove_atlan_tags(
                            asset_type=asset_cls,
                            qualified_name=updatable_asset.qualified_name,
                            atlan_tag_names=tag_names,
                        )
                    elif tag_operation == TagOperation.REPLACE:
                        client.asset._modify_tags(
                            asset_type=asset_cls,
                            qualified_name=updatable_asset.qualified_name,
                            atlan_tag_names=tag_names,
                            propagate=tag_value.propagate if tag_value.propagate is not None else False,
                            remove_propagation_on_delete=tag_value.remove_propagation_on_delete if tag_value.remove_propagation_on_delete is not None else True,
                            restrict_lineage_propagation=tag_value.restrict_lineage_propagation if tag_value.restrict_lineage_propagation is not None else False,
                            restrict_propagation_through_hierarchy=tag_value.restrict_propagation_through_hierarchy if tag_value.restrict_propagation_through_hierarchy is not None else False,
                            modification_type="replace",
                            save_parameters={
                                "replace_atlan_tags": True,
                                "append_atlan_tags": False,
                            },
                        )

                    result["updated_count"] += 1
                    logger.info(
                        f"Successfully performed '{tag_operation.value}' tag operation on asset: {updatable_asset.qualified_name}"
                    )

                except Exception as e:
                    error_msg = f"Error updating tags on asset {updatable_asset.qualified_name}: {str(e)}"
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

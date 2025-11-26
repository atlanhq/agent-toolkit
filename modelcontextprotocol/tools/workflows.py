"""Tools for retrieving and managing workflows in Atlan.

Naming Convention Note:
The Argo/Kubernetes API uses terminology that can be confusing:
- "WorkflowTemplate" (kind="WorkflowTemplate") = workflow (template definition)
- "Workflow" (kind="Workflow") = workflow_run (executed instance/run)

Throughout this module:
- "workflow" refers to WorkflowTemplate (kind="WorkflowTemplate") - the template definition
- "workflow_run" refers to Workflow (kind="Workflow") - an executed instance/run
- The extract_workflow_metadata() function returns fields prefixed with "run_*" for execution data
  and "workflow_*" for workflow-level metadata to clearly distinguish between the two.
"""

import logging
from typing import Dict, Any, Optional, Union, List

from client import get_atlan_client
from pyatlan.model.enums import WorkflowPackage, AtlanWorkflowPhase
from pyatlan.model.workflow import Workflow, WorkflowSchedule

# from dotenv import load_dotenv

# load_dotenv(dotenv_path="/Users/christopher.tin/Repos/.env")

logger = logging.getLogger(__name__)


def _result_to_dict(result: Any, include_dag: bool = False) -> Optional[Dict[str, Any]]:
    """
    Process a workflow or workflow_run object into a standardized dictionary format.

    Note: There is a naming confusion in the Argo/Kubernetes API:
    - "WorkflowTemplate" (kind="WorkflowTemplate") = workflow (template definition)
    - "Workflow" (kind="Workflow") = workflow_run (executed instance/run)
    
    This function handles both types and returns standardized metadata dictionaries.

    Args:
        result: The workflow or workflow_run object from PyAtlan (WorkflowSearchResult or Workflow).
        include_dag: If True, includes the workflow DAG in the output. This only applies if the input is a workflow (WorkflowTemplate).
            For workflow_run instances, this parameter has no effect.
    Returns:
        Optional[Dict[str, Any]]: Serialized workflow or workflow_run dictionary using Pydantic's dict() method.
            Returns None for unsupported workflow types. Returns empty dict {} if result is None or conversion fails.
    """
    if result is None:
        return {}
    
    try:
        dict_repr = result.dict(by_alias=True, exclude_unset=True)
    except (AttributeError, TypeError) as e:
        logger.warning(f"Failed to convert result to dict: {e}")
        return {}
    source = dict_repr.get("_source", None)
    if source is None:
        return dict_repr
    
    source_type = source.get("kind", None)
    if source_type == "Workflow":
        return extract_workflow_metadata(dict_repr)
    elif source_type == "WorkflowTemplate":
        return extract_workflow_template_metadata(dict_repr, include_dag=include_dag)
    else:
        logger.warning(f"Unsupported workflow type: {source_type}")
        return None  # Unsupported workflow type


def extract_workflow_template_metadata(dict_repr: Dict[str, Any], include_dag: bool = False) -> Dict[str, Any]:
    """
    Extract useful metadata from a workflow (WorkflowTemplate).

    Note: In Argo terminology, "WorkflowTemplate" (kind="WorkflowTemplate") is a workflow (template definition).
    This function extracts workflow metadata including package info, source system, certification status, etc.

    Args:
        dict_repr: The workflow object from the workflows array (kind="WorkflowTemplate")
        include_dag: If True, includes the workflow DAG (workflow_steps and workflow_spec) in the output.
            When False, returns only essential metadata fields.

    Returns:
        Dictionary containing extracted workflow metadata with fields like:
            - template_name, package_name, package_version
            - source_system, source_category, workflow_type
            - certified, verified flags
            - creator/modifier information
            - If include_dag=True: workflow_steps and workflow_spec
    """
    source = dict_repr.get("_source") or {}
    metadata = source.get('metadata') or {}
    labels = metadata.get('labels') or {}
    annotations = metadata.get('annotations') or {}

    base_output = {
            'template_name': metadata.get('name'),
            'package_name': annotations.get('package.argoproj.io/name'),
            'package_version': labels.get('package.argoproj.io/version'),
            'source_system': labels.get('orchestration.atlan.com/source'),
            'source_category': labels.get('orchestration.atlan.com/sourceCategory'),
            'workflow_type': labels.get('orchestration.atlan.com/type'),
            'certified': labels.get('orchestration.atlan.com/certified') == 'true',
            'verified': labels.get('orchestration.atlan.com/verified') == 'true',
            'creator_email': labels.get('workflows.argoproj.io/creator-email'),
            'creator_username': labels.get('workflows.argoproj.io/creator-preferred-username'),
            'modifier_email': labels.get('workflows.argoproj.io/modifier-email'),
            'modifier_username': labels.get('workflows.argoproj.io/modifier-preferred-username'),
            'creation_timestamp': metadata.get('creationTimestamp'),
            'package_author': annotations.get('package.argoproj.io/author'),
            'package_description': annotations.get('package.argoproj.io/description'),
            'package_repository': annotations.get('package.argoproj.io/repository')
        }

    if not include_dag:
        return base_output
    else:
        return {
            **base_output,
            'workflow_steps': annotations.get('orchestration.atlan.com/workflow-steps'),
            'workflow_spec': source.get('spec')
        }

def extract_workflow_metadata(dict_repr: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract comprehensive metadata from a workflow_run (Workflow executed instance/run).

    Note: In Argo terminology, "Workflow" (kind="Workflow") is a workflow_run (executed instance/run).
    This is different from "WorkflowTemplate" which is a workflow (template definition).

    The returned dictionary uses a two-tier naming convention:
    - Fields prefixed with "run_*" contain execution-specific metadata (phase, timing, resource usage)
    - Fields prefixed with "workflow_*" contain workflow-level metadata (template reference, package, creator)

    Args:
        dict_repr: The workflow_run object dictionary representation (kind="Workflow")

    Returns:
        Dictionary containing comprehensive workflow_run metadata with fields:
            Run Metadata (execution-specific):
            - run_id: Unique identifier for this run
            - run_phase: Execution phase (Succeeded, Running, Failed, etc.)
            - run_started_at, run_finished_at: Execution timestamps
            - run_estimated_duration, run_progress: Execution progress
            - run_cpu_usage, run_memory_usage: Resource usage
            
            Workflow Metadata (workflow-level):
            - workflow_id: Reference to the workflow (template) used
            - workflow_package_name: Package identifier
            - workflow_cron_schedule, workflow_cron_timezone: Scheduling info
            - workflow_creator_*, workflow_modifier_*: Ownership information
            - workflow_creation_timestamp, workflow_archiving_status: Lifecycle info
    """
    source = dict_repr.get("_source") or {}
    metadata = source.get('metadata') or {}
    labels = metadata.get('labels') or {}
    annotations = metadata.get('annotations') or {}
    status = source.get('status') or {}

    return {
        # Run Metadata
        'run_id': dict_repr.get('_id') or metadata.get('name'),
        'run_phase': status.get('phase'),
        'run_started_at': status.get('startedat') or status.get('startedAt'),
        'run_finished_at': status.get('finishedat') or status.get('finishedAt'),
        'run_estimated_duration': status.get('estimatedDuration'),
        'run_progress': status.get('progress'),
        'run_cpu_usage': status.get('resourcesDuration', {}).get('cpu'),
        'run_memory_usage': status.get('resourcesDuration', {}).get('memory'),

        # Workflow Metadata
        'workflow_id': labels.get('workflows.argoproj.io/workflow-template'),
        # 'cron_workflow': labels.get('workflows.argoproj.io/cron-workflow'),
        'workflow_package_name': annotations.get('package.argoproj.io/name'),
        'workflow_cron_schedule': annotations.get('orchestration.atlan.com/schedule'),
        'workflow_cron_timezone': annotations.get('orchestration.atlan.com/timezone'),
        'workflow_creator_id': labels.get('workflows.argoproj.io/creator'),
        'workflow_creator_email': labels.get('workflows.argoproj.io/creator-email'),
        'workflow_creator_username': labels.get('workflows.argoproj.io/creator-preferred-username'),
        'workflow_modifier_id': labels.get('workflows.argoproj.io/modifier'),
        'workflow_modifier_email': labels.get('workflows.argoproj.io/modifier-email'),
        'workflow_modifier_username': labels.get('workflows.argoproj.io/modifier-preferred-username'),
        'workflow_creation_timestamp': metadata.get('creationTimestamp'),
        'workflow_archiving_status': labels.get('workflows.argoproj.io/workflow-archiving-status')
    }


def get_workflow_package_names() -> List[str]:
    """
    Get the values of all workflow packages. 
    """
    return [pkg.value for pkg in WorkflowPackage]

def get_workflows_by_type(workflow_package_name: Union[WorkflowPackage, str], max_results: int = 10) -> Dict[str, Any]:
    """
    Retrieve workflows (WorkflowTemplate) by type (workflow package name).

    Args:
        workflow_package_name (Union[WorkflowPackage, str]): Workflow package type (e.g., WorkflowPackage.SNOWFLAKE or "atlan-snowflake").
        max_results (int, optional): Maximum number of workflows to return. Defaults to 10.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - workflows: List of workflows (WorkflowTemplate) with their configurations
            - total: Total count of workflows
            - error: None if no error occurred, otherwise the error message

    Examples:
        # Get Snowflake workflows
        from pyatlan.model.enums import WorkflowPackage
        result = get_workflows_by_type(WorkflowPackage.SNOWFLAKE)

        # Get workflows with custom limit
        result = get_workflows_by_type(WorkflowPackage.BIGQUERY, max_results=50)
    """
    logger.info(f"Starting workflow retrieval with workflow_package_name={workflow_package_name}, max_results={max_results}")

    try:
        client = get_atlan_client()

        # Retrieve workflows using the pyatlan SDK
        logger.debug(f"Calling client.workflow.find_by_type() with workflow_package_name={workflow_package_name}")
        results = client.workflow.find_by_type(prefix=workflow_package_name, max_results=max_results)

        logger.info(f"Successfully retrieved workflows")

        # Process the response
        workflows = results if results else []
        total = len(workflows) if workflows else 0

        # Extract key workflow information
        processed_workflows = [_result_to_dict(workflow) for workflow in workflows]

        return {
            "workflows": processed_workflows,
            "total": total,
            "error": None,
        }

    except Exception as e:
        error_msg = f"Failed to retrieve workflows: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "workflows": [],
            "total": 0,
            "error": error_msg,
        }


def get_workflow_by_id(id: str) -> Dict[str, Any]:
    """
    Retrieve a specific workflow (WorkflowTemplate) by its ID.

    Args:
        id (str): The unique identifier (ID) of the workflow (e.g., 'atlan-snowflake-miner-1714638976').

    Returns:
        Dict[str, Any]: Dictionary containing:
            - workflow: The workflow (WorkflowTemplate) object with its configuration, or None if not found
            - error: None if no error occurred, otherwise the error message

    Examples:
        # Get a specific workflow by ID
        result = get_workflow_by_id("atlan-snowflake-miner-1714638976")
    """
    logger.info(f"Retrieving workflow with ID: {id}")

    try:
        if not id:
            raise ValueError("id cannot be empty")

        client = get_atlan_client()

        # Retrieve workflow using the pyatlan SDK
        logger.debug(f"Calling client.workflow.find_by_id() with id={id}")
        workflow = client.workflow.find_by_id(id=id)

        if workflow is None:
            logger.warning(f"Workflow with ID '{id}' not found")
            return {
                "workflow": None,
                "error": f"Workflow with ID '{id}' not found",
            }

        logger.info(f"Successfully retrieved workflow with ID: {id}")
        processed_workflow = _result_to_dict(workflow, include_dag=True)

        return {
            "workflow": processed_workflow,
            "error": None,
        }

    except Exception as e:
        error_msg = f"Failed to retrieve workflow with ID '{id}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "workflow": None,
            "error": error_msg,
        }


def get_workflow_runs(
    workflow_name: Optional[str] = None,
    workflow_phase: Optional[Union[AtlanWorkflowPhase, str]] = None,
    status: Optional[Union[List[AtlanWorkflowPhase], List[str]]] = None,
    started_at: Optional[str] = None,
    finished_at: Optional[str] = None,
    from_: int = 0,
    size: int = 100,
) -> Dict[str, Any]:
    """
    Retrieve workflow_runs with flexible filtering options.

    This function supports two main use cases:
    1. Filter by specific workflow name and phase (single workflow)
    2. Filter across all workflows by status list and optional time ranges

    Args:
        workflow_name (str, optional): Name of the workflow (template) as displayed in the UI 
            (e.g., 'atlan-snowflake-miner-1714638976'). If provided, filters runs for that specific workflow.
        workflow_phase (Union[AtlanWorkflowPhase, str], optional): Phase of the workflow_run 
            (e.g., Succeeded, Running, Failed). Required if workflow_name is provided and status is not.
        status (Union[List[AtlanWorkflowPhase], List[str]], optional): List of workflow_run phases to filter by
            (e.g., ['Succeeded', 'Failed']). Required if workflow_name is not provided. Can also be used 
            with workflow_name (will use first item from list as workflow_phase).
        started_at (str, optional): Lower bound on 'status.startedAt' timestamp. Accepts:
            - Relative time format: 'now-2h', 'now-24h', 'now-7d', 'now-30d'
            - ISO 8601 format: '2024-01-01T00:00:00Z'
            Only used when workflow_name is not provided.
        finished_at (str, optional): Lower bound on 'status.finishedAt' timestamp. Accepts:
            - Relative time format: 'now-1h', 'now-12h'
            - ISO 8601 format: '2024-01-01T00:00:00Z'
            Only used when workflow_name is not provided.
        from_ (int, optional): Starting index of the search results. Defaults to 0.
        size (int, optional): Maximum number of search results to return. Defaults to 100.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - runs: List of workflow_runs with their details
            - total: Total count of workflow_runs
            - error: None if no error occurred, otherwise the error message

    Examples:
        # Get succeeded workflow_runs for a specific workflow
        from pyatlan.model.enums import AtlanWorkflowPhase
        result = get_workflow_runs("atlan-snowflake-miner-1714638976", workflow_phase=AtlanWorkflowPhase.SUCCESS)

        # Get running workflow_runs for a specific workflow
        result = get_workflow_runs("atlan-snowflake-miner-1714638976", workflow_phase="Running")

        # Get succeeded workflow_runs from the last 2 hours (across all workflows)
        result = get_workflow_runs(status=["Succeeded"], started_at="now-2h")

        # Get failed workflow_runs with both time filters (across all workflows)
        result = get_workflow_runs(
            status=["Failed"],
            started_at="now-24h",
            finished_at="now-1h"
        )

        # Get multiple statuses (across all workflows)
        result = get_workflow_runs(status=["Succeeded", "Failed"], started_at="now-7d")
    """
    logger.info(
        f"Retrieving workflow runs: workflow_name={workflow_name}, workflow_phase={workflow_phase}, "
        f"status={status}, started_at={started_at}, finished_at={finished_at}, from_={from_}, size={size}"
    )

    try:
        client = get_atlan_client()

        # Route based on whether workflow_name is provided
        if workflow_name:
            # Use get_runs() API - single workflow, single phase
            if not workflow_phase and not status:
                raise ValueError("Either workflow_phase or status must be provided when workflow_name is specified")
            
            # Use workflow_phase if provided, otherwise use first item from status list
            phase_to_use = workflow_phase
            if not phase_to_use and status:
                phase_to_use = status[0] if isinstance(status, list) and len(status) > 0 else None
            
            if not phase_to_use:
                raise ValueError("workflow_phase or status must be provided when workflow_name is specified")

            # Convert string to AtlanWorkflowPhase enum if needed
            if isinstance(phase_to_use, str):
                try:
                    phase_to_use = AtlanWorkflowPhase(phase_to_use)
                except ValueError:
                    # Try case-insensitive match
                    for phase in AtlanWorkflowPhase:
                        if phase.value.upper() == phase_to_use.upper():
                            phase_to_use = phase
                            break
                    else:
                        raise ValueError(f"Invalid workflow phase: {phase_to_use}")

            # Retrieve workflow runs using the pyatlan SDK
            logger.debug(f"Calling client.workflow.get_runs() with workflow_name={workflow_name}, workflow_phase={phase_to_use}")
            response = client.workflow.get_runs(
                workflow_name=workflow_name,
                workflow_phase=phase_to_use,
                from_=from_,
                size=size,
            )

            logger.info("Successfully retrieved workflow runs")
        else:
            # Use find_runs_by_status_and_time_range() API - all workflows, status list, time ranges
            if not status:
                raise ValueError("status must be provided when workflow_name is not specified")

            # Convert string statuses to AtlanWorkflowPhase enums if needed
            status_list = []
            for s in status:
                if isinstance(s, str):
                    try:
                        status_list.append(AtlanWorkflowPhase(s))
                    except ValueError:
                        # Try case-insensitive match
                        for phase in AtlanWorkflowPhase:
                            if phase.value.upper() == s.upper():
                                status_list.append(phase)
                                break
                        else:
                            raise ValueError(f"Invalid workflow phase: {s}")
                else:
                    status_list.append(s)

            # Retrieve workflow runs using the pyatlan SDK
            logger.debug(
                f"Calling client.workflow.find_runs_by_status_and_time_range() with "
                f"status={status_list}, started_at={started_at}, finished_at={finished_at}"
            )
            response = client.workflow.find_runs_by_status_and_time_range(
                status=status_list,
                started_at=started_at,
                finished_at=finished_at,
                from_=from_,
                size=size,
            )

            logger.info("Successfully retrieved workflow runs by status and time range")

        # Process the response
        runs = []
        total = 0
        if response and response.hits and response.hits.hits:
            runs = response.hits.hits
            # Handle total - it can be a dict with 'value' key or an object with .value attribute
            total_obj = response.hits.total
            if total_obj:
                if isinstance(total_obj, dict):
                    total = total_obj.get("value", len(runs))
                elif hasattr(total_obj, "value"):
                    total = total_obj.value
                else:
                    total = len(runs)
            else:
                total = len(runs)

        # Extract key run information using _result_to_dict for proper serialization
        processed_runs = []
        for run in runs:
            processed_run = _result_to_dict(run)
            processed_runs.append(processed_run)

        return {
            "runs": processed_runs,
            "total": total,
            "error": None,
        }

    except Exception as e:
        error_msg = f"Failed to retrieve workflow runs: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "runs": [],
            "total": 0,
            "error": error_msg,
        }


import logging
from typing import Optional, Dict, Any

from client import get_atlan_client
from pyatlan.model.enums import AtlanWorkflowPhase

logger = logging.getLogger(__name__)


def _parse_workflow_phase(phase: str) -> Optional[AtlanWorkflowPhase]:
    """Convert workflow phase string to enum."""
    if not phase:
        return None

    phase_mapping = {
        "succeeded": AtlanWorkflowPhase.SUCCESS,
        "success": AtlanWorkflowPhase.SUCCESS,
        "running": AtlanWorkflowPhase.RUNNING,
        "failed": AtlanWorkflowPhase.FAILED,
        "pending": AtlanWorkflowPhase.PENDING,
        "error": AtlanWorkflowPhase.ERROR,
    }

    phase_lower = phase.lower()
    if phase_lower in phase_mapping:
        return phase_mapping[phase_lower]

    try:
        return AtlanWorkflowPhase[phase.upper()]
    except KeyError:
        logger.warning(f"Invalid workflow phase: {phase}")
        return None


def _normalize_time(time_str: Optional[str]) -> Optional[str]:
    """
    Normalize time string to format accepted by SDK.

    Supports:
    - "now" or "now-Xh" format (passed directly)
    - Epoch timestamps in milliseconds as strings (passed directly)
    """
    if not time_str:
        return None

    # Pass "now-Xh" format or epoch timestamp directly
    if isinstance(time_str, str) and (time_str.startswith("now") or time_str.isdigit()):
        return time_str

    # If format is not recognized, return as-is (SDK may handle it)
    logger.warning(f"Unrecognized time format: {time_str}, returning as-is")
    return time_str


def get_workflow_runs(
    workflow_name: Optional[str] = None,
    workflow_phase: Optional[str] = None,
    workflow_run_id: Optional[str] = None,
    from_: int = 0,
    size: int = 100,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve workflow runs based on various criteria.

    Args:
        workflow_name: Name of the workflow as displayed in the UI.
        workflow_phase: Phase/status of the workflow run.
            Valid values: "Success", "Succeeded", "Running", "Failed", "Pending", "Error"
        workflow_run_id: Specific workflow run ID to retrieve.
        from_: Starting index of the search results. Defaults to 0.
        size: Maximum number of search results to return. Defaults to 100.
        start_time: Start time for filtering runs.
            Supports: "now-Xh" format (e.g., "now-24h") or epoch milliseconds (string).
        end_time: End time for filtering runs.
            Supports: "now-Xh" format (e.g., "now") or epoch milliseconds (string).

    Returns:
        Dict containing runs, total count, and error (if any).
    """
    try:
        client = get_atlan_client()

        # Handle specific run ID lookup
        if workflow_run_id:
            logger.info(f"Retrieving workflow run by ID: {workflow_run_id}")
            try:
                run = client.workflow.get_run(workflow_run_id=workflow_run_id)
                return {
                    "runs": [run] if run else [],
                    "total": 1 if run else 0,
                    "error": None
                    if run
                    else f"No workflow run found with ID: {workflow_run_id}",
                }
            except Exception as e:
                logger.error(f"Error retrieving workflow run by ID: {str(e)}")
                return {"runs": [], "total": 0, "error": str(e)}

        # Convert phase string to enum
        phase_enum = _parse_workflow_phase(workflow_phase) if workflow_phase else None

        # Use find_runs_by_status_and_time_range when phase or time range is provided
        # (SDK requires status parameter - if no phase specified, use all phases)
        if phase_enum or start_time or end_time:
            logger.info(
                f"Searching workflows: phase={workflow_phase or 'all'}, "
                f"start_time={start_time}, end_time={end_time}, "
                f"workflow_name={workflow_name or 'all'}"
            )

            try:
                # Normalize time formats
                started_at = _normalize_time(start_time)
                finished_at = _normalize_time(end_time)

                # Build status list - use specified phase or all phases if none specified
                if phase_enum:
                    status_list = [phase_enum]
                else:
                    # If no phase specified but time range is provided, search all phases
                    status_list = [
                        AtlanWorkflowPhase.SUCCESS,
                        AtlanWorkflowPhase.RUNNING,
                        AtlanWorkflowPhase.FAILED,
                        AtlanWorkflowPhase.PENDING,
                        AtlanWorkflowPhase.ERROR,
                    ]

                # Call SDK method
                results = client.workflow.find_runs_by_status_and_time_range(
                    status=status_list,
                    started_at=started_at,
                    finished_at=finished_at,
                    from_=from_,
                    size=size,
                )

                runs = list(results) if results else []

                # Filter by workflow name if provided
                if workflow_name:
                    filtered_runs = []
                    for run in runs:
                        try:
                            if hasattr(run, "source") and hasattr(run.source, "spec"):
                                template_ref = run.source.spec.workflow_template_ref
                                run_name = None
                                if hasattr(template_ref, "name"):
                                    run_name = template_ref.name
                                elif isinstance(template_ref, dict):
                                    run_name = template_ref.get("name")

                                if run_name == workflow_name:
                                    filtered_runs.append(run)
                        except (AttributeError, TypeError):
                            continue
                    runs = filtered_runs
                    logger.info(
                        f"Filtered to {len(runs)} workflows matching name '{workflow_name}'"
                    )

                return {"runs": runs, "total": len(runs), "error": None}

            except Exception as e:
                logger.error(f"Error retrieving workflow runs: {str(e)}")
                logger.exception("Exception details:")
                return {"runs": [], "total": 0, "error": str(e)}

        # Use get_runs for workflow name only (no phase/time filters)
        if workflow_name:
            logger.info(f"Retrieving workflow runs for '{workflow_name}'")
            try:
                runs_response = client.workflow.get_runs(
                    workflow_name=workflow_name,
                    workflow_phase=phase_enum,
                    from_=from_,
                    size=size,
                )
                runs = list(runs_response) if runs_response else []
                return {"runs": runs, "total": len(runs), "error": None}
            except Exception as e:
                logger.error(f"Error retrieving workflow runs: {str(e)}")
                return {"runs": [], "total": 0, "error": str(e)}

        # No criteria provided
        return {
            "runs": [],
            "total": 0,
            "error": "At least one of workflow_name, workflow_run_id, workflow_phase, start_time, or end_time must be provided",
        }

    except Exception as e:
        logger.error(f"Unexpected error in get_workflow_runs: {str(e)}")
        return {"runs": [], "total": 0, "error": str(e)}

"""
Atlan MCP Server Resources

This module provides access to configuration data, templates,
and other resources for the Atlan MCP server.
"""

from .config import (
    atlan_config_resource,
    connection_info_resource,
)
from .templates import (
    data_governance_templates_resource,
    quality_assessment_template_resource,
    lineage_documentation_template_resource,
)
from .reports import (
    asset_summary_report_resource,
    quality_metrics_report_resource,
)

__all__ = [
    "atlan_config_resource",
    "connection_info_resource",
    "data_governance_templates_resource", 
    "quality_assessment_template_resource",
    "lineage_documentation_template_resource",
    "asset_summary_report_resource",
    "quality_metrics_report_resource",
]
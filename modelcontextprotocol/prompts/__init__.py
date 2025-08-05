"""
Atlan MCP Server Prompts

This module contains reusable prompt templates for data analysis,
documentation, and governance workflows.
"""

from .data_analysis import (
    data_quality_analysis_prompt,
    lineage_documentation_prompt,
    asset_comparison_prompt,
)
from .governance import (
    compliance_assessment_prompt,
    policy_recommendation_prompt,
)

__all__ = [
    "data_quality_analysis_prompt",
    "lineage_documentation_prompt", 
    "asset_comparison_prompt",
    "compliance_assessment_prompt",
    "policy_recommendation_prompt",
]
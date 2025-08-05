"""
Data analysis prompts for Atlan assets.
"""

from typing import Dict, Any, Optional
from fastmcp import Context


async def data_quality_analysis_prompt(
    asset_type: str,
    conditions: Optional[Dict[str, Any]] = None,
    focus_areas: Optional[list] = None,
    ctx: Optional[Context] = None
) -> str:
    """
    Generate a comprehensive data quality analysis prompt for Atlan assets.
    
    Args:
        asset_type: Type of asset to analyze (Table, Column, etc.)
        conditions: Search conditions for filtering assets
        focus_areas: Specific quality dimensions to focus on
        ctx: FastMCP context for logging
    """
    
    if ctx:
        await ctx.info(f"Generating data quality analysis prompt for {asset_type}")
    
    focus_list = focus_areas or [
        "Completeness", "Accuracy", "Consistency", "Timeliness", "Validity"
    ]
    
    conditions_text = ""
    if conditions:
        conditions_text = f"""
## Search Conditions Applied:
```json
{conditions}
```
"""
    
    return f"""# Data Quality Analysis for {asset_type} Assets

You are a data quality expert analyzing {asset_type} assets in Atlan. Please conduct a comprehensive quality assessment.

{conditions_text}

## Analysis Framework

### Focus Areas:
{chr(10).join(f"- **{area}**" for area in focus_list)}

### Quality Dimensions:

1. **Completeness Assessment**
   - Identify missing values and null percentages
   - Check for incomplete records or partial data
   - Assess coverage across different data segments

2. **Accuracy Validation**
   - Verify data formats and patterns
   - Check against business rules and constraints
   - Identify outliers and anomalies

3. **Consistency Analysis**
   - Compare data across related assets
   - Check for referential integrity
   - Validate standardization across systems

4. **Timeliness Evaluation**
   - Assess data freshness and update frequencies
   - Identify stale or outdated information
   - Check sync delays between systems

5. **Validity Verification**
   - Ensure compliance with data standards
   - Validate against business logic
   - Check for proper data classifications

## Expected Deliverables:

### 1. Executive Summary
- Overall quality score and trend analysis
- Critical issues requiring immediate attention
- Impact assessment on downstream systems

### 2. Detailed Findings
- Quality metrics by dimension
- Specific data issues with examples
- Root cause analysis where possible

### 3. Recommendations
- Prioritized action items with timelines
- Process improvements and automation opportunities
- Monitoring and alerting suggestions

### 4. Implementation Plan
- Step-by-step remediation approach
- Resource requirements and ownership
- Success metrics and validation criteria

Please provide actionable insights that will improve data reliability and trustworthiness across the organization.
"""


async def lineage_documentation_prompt(
    asset_guid: str,
    direction: str = "BOTH",
    include_impact: bool = True,
    ctx: Optional[Context] = None
) -> str:
    """
    Generate a prompt for creating comprehensive lineage documentation.
    
    Args:
        asset_guid: GUID of the asset to document
        direction: Lineage direction (UPSTREAM, DOWNSTREAM, BOTH)
        include_impact: Whether to include business impact analysis
        ctx: FastMCP context for logging
    """
    
    if ctx:
        await ctx.info(f"Creating lineage documentation prompt for asset {asset_guid}")
    
    impact_section = ""
    if include_impact:
        impact_section = """
### 5. Business Impact Analysis
- Critical business processes dependent on this data
- Stakeholder groups and their usage patterns
- Revenue or operational impact of data issues
- Change management considerations
"""
    
    return f"""# Data Lineage Documentation Request

Create comprehensive documentation for the data lineage of asset: `{asset_guid}`

## Documentation Scope
- **Lineage Direction**: {direction}
- **Include Business Impact**: {include_impact}
- **Focus**: End-to-end data flow with business context

## Required Documentation Sections:

### 1. Executive Summary
- High-level data flow overview (source → transformations → targets)
- Key business processes supported by this data
- Critical dependencies and potential failure points
- Data ownership and stewardship information

### 2. Source Systems Analysis
- Origin systems and data extraction methods
- Data collection frequency and timing
- Source data quality and reliability
- Access patterns and security considerations

### 3. Transformation Logic
- Detailed transformation rules and business logic
- Data cleansing and validation steps
- Aggregation and calculation methods
- Error handling and data recovery processes

### 4. Target Systems and Usage
- Destination systems and consumption patterns
- Data format requirements and constraints
- Performance considerations and SLAs
- Monitoring and alerting mechanisms
{impact_section}
### 6. Technical Specifications
- Data schemas and field mappings
- Integration patterns and protocols
- Scalability and performance characteristics
- Security and compliance requirements

### 7. Operational Procedures
- Deployment and rollback procedures
- Monitoring and troubleshooting guides
- Disaster recovery and business continuity
- Maintenance and update schedules

## Documentation Standards:
- Use clear, business-friendly language
- Include visual diagrams where helpful
- Provide specific examples and use cases
- Format as structured markdown
- Include version control and change tracking

Please ensure the documentation serves both technical teams and business stakeholders effectively.
"""


async def asset_comparison_prompt(
    asset_guids: list,
    comparison_criteria: Optional[list] = None,
    ctx: Optional[Context] = None
) -> str:
    """
    Generate a prompt for comparing multiple Atlan assets.
    
    Args:
        asset_guids: List of asset GUIDs to compare
        comparison_criteria: Specific aspects to compare
        ctx: FastMCP context for logging
    """
    
    if ctx:
        await ctx.info(f"Creating asset comparison prompt for {len(asset_guids)} assets")
    
    criteria_list = comparison_criteria or [
        "Schema structure", "Data quality", "Usage patterns", 
        "Performance metrics", "Business context"
    ]
    
    assets_text = "\n".join(f"- {guid}" for guid in asset_guids)
    
    return f"""# Asset Comparison Analysis

Compare the following Atlan assets across multiple dimensions to identify similarities, differences, and optimization opportunities.

## Assets to Compare:
{assets_text}

## Comparison Framework:

### Analysis Dimensions:
{chr(10).join(f"- {criteria}" for criteria in criteria_list)}

### 1. Structural Comparison
- Schema differences and commonalities
- Field types, constraints, and relationships
- Indexing and partitioning strategies
- Data volume and growth patterns

### 2. Quality Assessment
- Data quality scores and trends
- Common quality issues across assets
- Completeness and accuracy metrics
- Validation rules and compliance status

### 3. Usage Analysis
- Access patterns and frequency
- User communities and stakeholders
- Query performance and optimization
- Integration points and dependencies

### 4. Business Context
- Purpose and business value
- Ownership and stewardship models
- Criticality and risk assessment
- Compliance and governance requirements

### 5. Technical Performance
- Storage utilization and costs
- Processing times and bottlenecks
- Scalability and resource requirements
- Maintenance overhead and complexity

## Expected Deliverables:

### Comparison Matrix
- Side-by-side feature comparison
- Strengths and weaknesses analysis
- Gap identification and recommendations

### Consolidation Opportunities
- Potential for asset merger or standardization
- Redundancy elimination strategies
- Resource optimization recommendations

### Best Practices
- Lessons learned from high-performing assets
- Standards and patterns to replicate
- Governance and quality improvements

### Action Plan
- Prioritized improvement initiatives
- Resource requirements and timelines
- Success metrics and validation criteria

Focus on actionable insights that can drive standardization, improve efficiency, and reduce technical debt.
"""
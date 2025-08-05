"""
Report generation resources for Atlan assets.
"""

import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastmcp import Context


async def asset_summary_report_resource(
    asset_type: Optional[str] = None,
    timeframe_days: int = 30,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Generate a summary report of assets in the Atlan environment.
    
    Args:
        asset_type: Specific asset type to report on (optional)
        timeframe_days: Number of days to include in the report
        ctx: FastMCP context for logging
        
    Returns:
        Dictionary containing report text
    """
    
    if ctx:
        report_scope = f"{asset_type} assets" if asset_type else "all assets"
        await ctx.info(f"Generating asset summary report for {report_scope}")
    
    # Mock data for demonstration - in real implementation, this would query Atlan
    end_date = datetime.now()
    start_date = end_date - timedelta(days=timeframe_days)
    
    # Generate sample report data
    report_data = {
        "report_metadata": {
            "generated_at": end_date.isoformat(),
            "timeframe": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "days": timeframe_days
            },
            "scope": asset_type or "all_assets",
            "report_type": "asset_summary"
        },
        "executive_summary": {
            "total_assets": 12547,
            "new_assets": 234,
            "updated_assets": 1456,
            "quality_score": 87.3,
            "compliance_score": 94.2
        },
        "asset_breakdown": {
            "tables": 4521,
            "columns": 45210,
            "views": 892,
            "databases": 23,
            "schemas": 156,
            "connections": 12,
            "glossary_terms": 789,
            "files": 1944
        },
        "quality_metrics": {
            "completeness": {
                "score": 89.5,
                "trend": "+2.3%",
                "critical_issues": 12
            },
            "accuracy": {
                "score": 85.1,
                "trend": "+1.8%",
                "critical_issues": 8
            },
            "consistency": {
                "score": 91.2,
                "trend": "-0.5%",
                "critical_issues": 5
            },
            "timeliness": {
                "score": 83.7,
                "trend": "+3.1%",
                "critical_issues": 15
            }
        },
        "governance_status": {
            "classified_assets": 89.3,
            "owned_assets": 76.8,
            "documented_assets": 68.4,
            "certified_assets": 45.2
        },
        "usage_analytics": {
            "most_accessed_assets": [
                {"name": "customer_transactions", "access_count": 1247},
                {"name": "product_catalog", "access_count": 892},
                {"name": "user_profiles", "access_count": 756}
            ],
            "trending_assets": [
                {"name": "new_marketing_data", "growth": "+45%"},
                {"name": "sales_analytics", "growth": "+32%"},
                {"name": "customer_insights", "growth": "+28%"}
            ]
        },
        "compliance_summary": {
            "gdpr_compliance": 96.5,
            "data_retention_compliance": 92.1,
            "access_control_compliance": 98.3,
            "audit_trail_completeness": 94.7
        },
        "recommendations": [
            {
                "priority": "high",
                "category": "data_quality",
                "description": "Implement automated quality monitoring for critical tables",
                "estimated_effort": "2-3 weeks",
                "expected_impact": "15% quality improvement"
            },
            {
                "priority": "medium", 
                "category": "governance",
                "description": "Increase asset documentation coverage",
                "estimated_effort": "4-6 weeks",
                "expected_impact": "Improved data discovery and usage"
            },
            {
                "priority": "medium",
                "category": "certification",
                "description": "Establish certification workflow for critical assets",
                "estimated_effort": "3-4 weeks", 
                "expected_impact": "Enhanced data trust and reliability"
            }
        ]
    }
    
    # Format as a readable report
    report_text = f"""# Asset Summary Report

## Report Overview
- **Generated**: {report_data['report_metadata']['generated_at']}
- **Timeframe**: {report_data['report_metadata']['timeframe']['start_date']} to {report_data['report_metadata']['timeframe']['end_date']} ({timeframe_days} days)
- **Scope**: {asset_type or 'All Asset Types'}

## Executive Summary

### Key Metrics
- **Total Assets**: {report_data['executive_summary']['total_assets']:,}
- **New Assets**: {report_data['executive_summary']['new_assets']:,} 
- **Updated Assets**: {report_data['executive_summary']['updated_assets']:,}
- **Overall Quality Score**: {report_data['executive_summary']['quality_score']}%
- **Compliance Score**: {report_data['executive_summary']['compliance_score']}%

## Asset Inventory

| Asset Type | Count |
|------------|-------|
| Tables | {report_data['asset_breakdown']['tables']:,} |
| Columns | {report_data['asset_breakdown']['columns']:,} |
| Views | {report_data['asset_breakdown']['views']:,} |
| Databases | {report_data['asset_breakdown']['databases']:,} |
| Schemas | {report_data['asset_breakdown']['schemas']:,} |
| Connections | {report_data['asset_breakdown']['connections']:,} |
| Glossary Terms | {report_data['asset_breakdown']['glossary_terms']:,} |
| Files | {report_data['asset_breakdown']['files']:,} |

## Data Quality Dashboard

### Quality Dimensions
- **Completeness**: {report_data['quality_metrics']['completeness']['score']}% ({report_data['quality_metrics']['completeness']['trend']})
- **Accuracy**: {report_data['quality_metrics']['accuracy']['score']}% ({report_data['quality_metrics']['accuracy']['trend']})
- **Consistency**: {report_data['quality_metrics']['consistency']['score']}% ({report_data['quality_metrics']['consistency']['trend']})
- **Timeliness**: {report_data['quality_metrics']['timeliness']['score']}% ({report_data['quality_metrics']['timeliness']['trend']})

### Critical Issues Summary
- Completeness: {report_data['quality_metrics']['completeness']['critical_issues']} issues
- Accuracy: {report_data['quality_metrics']['accuracy']['critical_issues']} issues  
- Consistency: {report_data['quality_metrics']['consistency']['critical_issues']} issues
- Timeliness: {report_data['quality_metrics']['timeliness']['critical_issues']} issues

## Governance Status

- **Classified Assets**: {report_data['governance_status']['classified_assets']}%
- **Assets with Owners**: {report_data['governance_status']['owned_assets']}%
- **Documented Assets**: {report_data['governance_status']['documented_assets']}%
- **Certified Assets**: {report_data['governance_status']['certified_assets']}%

## Usage Analytics

### Most Accessed Assets
{chr(10).join(f"- {asset['name']}: {asset['access_count']:,} accesses" for asset in report_data['usage_analytics']['most_accessed_assets'])}

### Trending Assets (Growth)
{chr(10).join(f"- {asset['name']}: {asset['growth']} growth" for asset in report_data['usage_analytics']['trending_assets'])}

## Compliance Summary

- **GDPR Compliance**: {report_data['compliance_summary']['gdpr_compliance']}%
- **Data Retention Compliance**: {report_data['compliance_summary']['data_retention_compliance']}%
- **Access Control Compliance**: {report_data['compliance_summary']['access_control_compliance']}%
- **Audit Trail Completeness**: {report_data['compliance_summary']['audit_trail_completeness']}%

## Recommendations

{chr(10).join(f"### {rec['priority'].title()} Priority: {rec['category'].replace('_', ' ').title()}{chr(10)}- **Description**: {rec['description']}{chr(10)}- **Estimated Effort**: {rec['estimated_effort']}{chr(10)}- **Expected Impact**: {rec['expected_impact']}{chr(10)}" for rec in report_data['recommendations'])}

## Next Steps

1. **Address Critical Quality Issues**: Focus on the {sum(metric['critical_issues'] for metric in report_data['quality_metrics'].values())} critical quality issues identified
2. **Improve Governance Coverage**: Increase documentation and certification rates
3. **Enhance Monitoring**: Implement automated monitoring for trending assets
4. **Compliance Review**: Address gaps in data retention and access controls

*Report generated by Atlan MCP Server*
"""
    
    return {"text": report_text}


async def quality_metrics_report_resource(
    metric_type: str = "overview",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Generate detailed data quality metrics report.
    
    Args:
        metric_type: Type of metrics report (overview, detailed, trends)
        ctx: FastMCP context for logging
        
    Returns:
        Dictionary containing quality metrics report
    """
    
    if ctx:
        await ctx.info(f"Generating {metric_type} quality metrics report")
    
    # Mock quality metrics data
    current_date = datetime.now()
    
    base_metrics = {
        "report_info": {
            "generated_at": current_date.isoformat(),
            "report_type": f"quality_metrics_{metric_type}",
            "coverage": "All critical datasets"
        },
        "overall_scores": {
            "completeness": 89.3,
            "accuracy": 85.7,
            "consistency": 91.2,
            "timeliness": 83.4,
            "validity": 87.9,
            "overall": 87.5
        },
        "dataset_breakdown": [
            {
                "dataset": "customer_data",
                "completeness": 94.2,
                "accuracy": 89.1,
                "consistency": 96.3,
                "timeliness": 87.5,
                "validity": 91.8,
                "overall": 91.8,
                "critical_issues": 3,
                "record_count": 2847563
            },
            {
                "dataset": "transaction_data", 
                "completeness": 97.8,
                "accuracy": 95.3,
                "consistency": 98.1,
                "timeliness": 89.2,
                "validity": 96.4,
                "overall": 95.4,
                "critical_issues": 1,
                "record_count": 15672890
            },
            {
                "dataset": "product_catalog",
                "completeness": 78.4,
                "accuracy": 72.1,
                "consistency": 83.7,
                "timeliness": 76.8,
                "validity": 79.3,
                "overall": 78.1,
                "critical_issues": 12,
                "record_count": 456789
            }
        ]
    }
    
    if metric_type == "overview":
        report_text = f"""# Data Quality Metrics Overview

## Summary (Generated: {current_date.strftime('%Y-%m-%d %H:%M')})

### Overall Quality Scores
- **Completeness**: {base_metrics['overall_scores']['completeness']}%
- **Accuracy**: {base_metrics['overall_scores']['accuracy']}%
- **Consistency**: {base_metrics['overall_scores']['consistency']}%
- **Timeliness**: {base_metrics['overall_scores']['timeliness']}%
- **Validity**: {base_metrics['overall_scores']['validity']}%
- **Overall Score**: {base_metrics['overall_scores']['overall']}%

### Dataset Quality Summary

| Dataset | Overall Score | Critical Issues | Record Count |
|---------|---------------|-----------------|--------------|
{chr(10).join(f"| {ds['dataset']} | {ds['overall']}% | {ds['critical_issues']} | {ds['record_count']:,} |" for ds in base_metrics['dataset_breakdown'])}

### Quality Distribution
- **High Quality (90%+)**: {len([ds for ds in base_metrics['dataset_breakdown'] if ds['overall'] >= 90])} datasets
- **Medium Quality (70-90%)**: {len([ds for ds in base_metrics['dataset_breakdown'] if 70 <= ds['overall'] < 90])} datasets  
- **Low Quality (<70%)**: {len([ds for ds in base_metrics['dataset_breakdown'] if ds['overall'] < 70])} datasets

### Action Items
- **Immediate Attention**: {sum(ds['critical_issues'] for ds in base_metrics['dataset_breakdown'])} critical issues across all datasets
- **Focus Areas**: Datasets with scores below 80% need improvement
- **Monitoring**: Continue tracking trends for all datasets
"""

    elif metric_type == "detailed":
        report_text = f"""# Detailed Data Quality Metrics Report

## Comprehensive Analysis (Generated: {current_date.strftime('%Y-%m-%d %H:%M')})

### Quality Dimension Analysis

#### Completeness Assessment
- **Overall Score**: {base_metrics['overall_scores']['completeness']}%
- **Trend**: Improving (+2.3% from last month)
- **Key Issues**: Missing values in optional fields, incomplete address data

#### Accuracy Validation  
- **Overall Score**: {base_metrics['overall_scores']['accuracy']}%
- **Trend**: Stable (+0.8% from last month)
- **Key Issues**: Email format validation, phone number standardization

#### Consistency Review
- **Overall Score**: {base_metrics['overall_scores']['consistency']}%
- **Trend**: Declining (-1.2% from last month)
- **Key Issues**: Cross-system data synchronization delays

#### Timeliness Monitoring
- **Overall Score**: {base_metrics['overall_scores']['timeliness']}%
- **Trend**: Improving (+3.1% from last month)
- **Key Issues**: Batch processing delays, real-time sync failures

#### Validity Checks
- **Overall Score**: {base_metrics['overall_scores']['validity']}%
- **Trend**: Stable (+0.3% from last month)
- **Key Issues**: Business rule violations, constraint validation failures

### Dataset Deep Dive

{chr(10).join(f'''#### {ds['dataset'].replace('_', ' ').title()}
- **Overall Quality**: {ds['overall']}%
- **Record Count**: {ds['record_count']:,}
- **Critical Issues**: {ds['critical_issues']}

**Quality Breakdown:**
- Completeness: {ds['completeness']}%
- Accuracy: {ds['accuracy']}%
- Consistency: {ds['consistency']}%
- Timeliness: {ds['timeliness']}%
- Validity: {ds['validity']}%
''' for ds in base_metrics['dataset_breakdown'])}

### Quality Rules Performance

#### Top Performing Rules
1. **Primary Key Uniqueness**: 99.8% compliance
2. **Required Field Validation**: 96.4% compliance  
3. **Data Type Validation**: 94.7% compliance

#### Underperforming Rules
1. **Email Format Validation**: 78.3% compliance
2. **Address Standardization**: 72.1% compliance
3. **Phone Number Format**: 69.8% compliance

### Recommendations

#### Immediate Actions (0-30 days)
- Fix critical data quality issues in product_catalog dataset
- Implement automated email validation
- Review and update address standardization rules

#### Medium-term Improvements (1-3 months)
- Establish real-time data quality monitoring
- Implement data quality SLAs and alerting
- Enhance cross-system consistency checks

#### Long-term Strategy (3-12 months)
- Deploy machine learning-based quality detection
- Establish predictive quality analytics
- Implement self-healing data pipelines
"""

    elif metric_type == "trends":
        # Generate 6 months of trend data
        months = []
        for i in range(6):
            month_date = current_date - timedelta(days=30*i)
            months.append({
                "month": month_date.strftime("%Y-%m"),
                "completeness": base_metrics['overall_scores']['completeness'] + (i * 0.5),
                "accuracy": base_metrics['overall_scores']['accuracy'] + (i * 0.3),
                "consistency": base_metrics['overall_scores']['consistency'] - (i * 0.2),
                "timeliness": base_metrics['overall_scores']['timeliness'] + (i * 0.7),
                "overall": base_metrics['overall_scores']['overall'] + (i * 0.4)
            })
        months.reverse()
        
        report_text = f"""# Data Quality Trends Report

## 6-Month Quality Trend Analysis (Generated: {current_date.strftime('%Y-%m-%d %H:%M')})

### Overall Quality Trends

| Month | Completeness | Accuracy | Consistency | Timeliness | Overall |
|-------|-------------|----------|-------------|------------|---------|
{chr(10).join(f"| {month['month']} | {month['completeness']:.1f}% | {month['accuracy']:.1f}% | {month['consistency']:.1f}% | {month['timeliness']:.1f}% | {month['overall']:.1f}% |" for month in months)}

### Trend Analysis

#### Improving Areas
- **Timeliness**: Steady improvement (+4.2% over 6 months)
- **Completeness**: Consistent growth (+3.0% over 6 months)
- **Accuracy**: Gradual improvement (+1.8% over 6 months)

#### Areas of Concern
- **Consistency**: Declining trend (-1.2% over 6 months)
- **Validity**: Plateauing performance (minimal change)

### Key Performance Indicators

#### Quality Score Distribution Over Time
- **Excellent (95%+)**: Increasing from 12% to 18% of datasets
- **Good (85-95%)**: Stable at approximately 45% of datasets
- **Fair (70-85%)**: Decreasing from 38% to 32% of datasets
- **Poor (<70%)**: Stable at approximately 5% of datasets

#### Monthly Quality Incidents
- **Critical Issues**: Decreasing from 45 to 28 per month
- **Medium Issues**: Stable at 120-130 per month
- **Minor Issues**: Increasing from 200 to 240 per month

### Predictive Insights

#### Expected Performance (Next 3 Months)
- **Overall Quality**: Projected to reach 90% by end of quarter
- **Completeness**: Expected to stabilize at 92-94%
- **Timeliness**: Target of 88-90% achievable with current trajectory

#### Risk Factors
- **Consistency**: Requires immediate attention to prevent further decline
- **Data Volume Growth**: 15% monthly increase may impact quality scores
- **System Migrations**: Planned infrastructure changes may temporarily affect metrics

### Recommendations

#### Immediate Focus
1. **Address Consistency Issues**: Implement cross-system validation
2. **Automate Quality Monitoring**: Reduce manual oversight burden
3. **Enhance Alerting**: Proactive issue detection and resolution

#### Strategic Initiatives
1. **Quality by Design**: Embed quality controls in data pipelines
2. **Predictive Quality**: Machine learning-based quality forecasting
3. **Self-Healing Systems**: Automated quality issue remediation
"""
    
    else:
        return {
            "text": f"Unknown metric type '{metric_type}'. Available types: overview, detailed, trends"
        }
    
    return {"text": report_text}
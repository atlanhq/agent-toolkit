"""
Template resources for data governance and documentation.
"""

from typing import Optional, Dict, Any
from fastmcp import Context


async def data_governance_templates_resource(
    template_type: str,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Provide data governance templates for various use cases.
    
    Args:
        template_type: Type of template (classification, quality_rules, etc.)
        ctx: FastMCP context for logging
        
    Returns:
        Dictionary containing template text
    """
    
    if ctx:
        await ctx.info(f"Loading {template_type} governance template")
    
    templates = {
        "data_classification": """# Data Classification Template

## Classification Schema

### 1. Public Data
- **Definition**: Information that can be freely shared with external parties
- **Examples**: Marketing materials, published research, public announcements
- **Handling**: No special restrictions
- **Retention**: As per business requirements

### 2. Internal Data  
- **Definition**: Information for internal business use only
- **Examples**: Employee directories, internal policies, project documentation
- **Handling**: Access limited to employees and authorized contractors
- **Retention**: 7 years or as per business requirements

### 3. Confidential Data
- **Definition**: Sensitive business information that could harm the organization if disclosed
- **Examples**: Financial data, strategic plans, customer lists, contracts
- **Handling**: 
  - Need-to-know access only
  - Encryption required for storage and transmission
  - Regular access reviews
- **Retention**: 10 years or as per regulatory requirements

### 4. Restricted Data
- **Definition**: Highly sensitive data protected by law or regulation
- **Examples**: PII, PHI, payment card data, social security numbers
- **Handling**:
  - Strict access controls with approval workflow
  - Encryption and tokenization required
  - Comprehensive audit logging
  - Regular compliance reviews
- **Retention**: As per regulatory requirements (varies by jurisdiction)

## Implementation Guidelines

### Required Metadata Fields:
- **Data Classification Level**: [Public|Internal|Confidential|Restricted]
- **Business Owner**: Person responsible for business decisions
- **Technical Owner**: Person responsible for technical implementation
- **Data Steward**: Person responsible for day-to-day management
- **Classification Date**: When classification was assigned
- **Review Date**: When classification should be reviewed
- **Retention Period**: How long data should be retained
- **Disposal Method**: How data should be disposed of

### Access Control Matrix:
| Classification | Internal Users | External Partners | Public Access |
|---------------|----------------|-------------------|---------------|
| Public        | ✓              | ✓                 | ✓             |
| Internal      | ✓              | Case-by-case      | ✗             |
| Confidential  | Need-to-know   | With NDA only     | ✗             |
| Restricted    | Explicit approval | With legal review | ✗           |

### Compliance Requirements:
- Regular classification reviews (annual for Confidential/Restricted)
- Data inventory and mapping
- Access audit trails
- Incident reporting procedures
- Staff training and awareness programs
""",

        "quality_rules": """# Data Quality Rules Template

## Quality Dimensions Framework

### 1. Completeness Rules
```yaml
completeness_rules:
  required_fields:
    - field_name: "customer_id"
      description: "Unique customer identifier"
      null_threshold: 0%
      
    - field_name: "email_address"
      description: "Customer email for communication"
      null_threshold: 5%
      
  record_completeness:
    minimum_populated_fields: 80%
    critical_fields_threshold: 95%
```

### 2. Accuracy Rules  
```yaml
accuracy_rules:
  format_validation:
    - field_name: "email_address"
      pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
      
    - field_name: "phone_number"
      pattern: "^\\+?[1-9]\\d{1,14}$"
      
  range_validation:
    - field_name: "age"
      min_value: 0
      max_value: 150
      
    - field_name: "transaction_amount"
      min_value: 0.01
      max_value: 1000000
      
  reference_data:
    - field_name: "country_code"
      reference_table: "country_codes"
      reference_field: "iso_code"
```

### 3. Consistency Rules
```yaml
consistency_rules:
  cross_field_validation:
    - rule_name: "birth_date_age_consistency"
      description: "Age should match calculated age from birth date"
      fields: ["birth_date", "age"]
      tolerance_days: 365
      
  cross_system_validation:
    - rule_name: "customer_data_sync"
      description: "Customer data should be consistent across CRM and billing"
      source_system: "CRM"
      target_system: "Billing"
      key_fields: ["customer_id"]
      comparison_fields: ["name", "email", "address"]
```

### 4. Timeliness Rules
```yaml
timeliness_rules:
  freshness_requirements:
    - dataset: "customer_transactions"
      max_age_hours: 2
      business_impact: "high"
      
    - dataset: "product_catalog"
      max_age_hours: 24
      business_impact: "medium"
      
  update_frequency:
    - dataset: "real_time_inventory"
      expected_frequency: "continuous"
      max_delay_minutes: 5
      
    - dataset: "daily_sales_summary"
      expected_frequency: "daily"
      expected_time: "06:00 UTC"
```

### 5. Validity Rules
```yaml
validity_rules:
  business_rules:
    - rule_name: "positive_inventory"
      description: "Inventory levels cannot be negative"
      expression: "quantity >= 0"
      
    - rule_name: "future_delivery_date"
      description: "Delivery date must be in the future"
      expression: "delivery_date > current_date"
      
  data_type_validation:
    - field_name: "order_date"
      expected_type: "datetime"
      format: "YYYY-MM-DD HH:MM:SS"
      
    - field_name: "product_price"
      expected_type: "decimal"
      precision: 2
```

## Quality Monitoring Implementation

### Automated Checks:
- Daily data quality scorecards
- Real-time threshold monitoring
- Anomaly detection algorithms
- Trend analysis and reporting

### Exception Handling:
- Quality issue escalation procedures
- Data quarantine processes
- Root cause analysis workflows
- Corrective action tracking

### Reporting and Metrics:
- Executive quality dashboards
- Detailed quality scorecards by dataset
- Trend analysis and improvement tracking
- Business impact assessment
""",

        "lineage_documentation": """# Data Lineage Documentation Template

## Executive Summary

### Data Asset Overview
- **Asset Name**: [Table/Dataset Name]
- **Business Purpose**: [Primary business use case]
- **Data Domain**: [Finance/Marketing/Operations/etc.]
- **Criticality Level**: [High/Medium/Low]
- **Update Frequency**: [Real-time/Hourly/Daily/Weekly]

### Key Stakeholders
- **Business Owner**: [Name and role]
- **Technical Owner**: [Name and role]  
- **Data Steward**: [Name and role]
- **Primary Consumers**: [Teams/systems that use this data]

## Source Systems Analysis

### Primary Data Sources
```yaml
source_systems:
  - system_name: "Customer CRM"
    connection_type: "Salesforce API"
    extraction_method: "Incremental sync"
    update_frequency: "Every 15 minutes"
    data_volume: "~1M records"
    
  - system_name: "E-commerce Platform"  
    connection_type: "Database direct"
    extraction_method: "CDC (Change Data Capture)"
    update_frequency: "Real-time"
    data_volume: "~500K transactions/day"
```

### Data Quality at Source
- **Completeness**: 95% of critical fields populated
- **Accuracy**: Regular validation against business rules
- **Consistency**: Standardized formats enforced
- **Reliability**: 99.9% uptime SLA

## Transformation Logic

### Data Processing Pipeline
```mermaid
graph LR
    A[Source Extract] --> B[Data Validation]
    B --> C[Business Rule Application]
    C --> D[Data Enrichment]
    D --> E[Quality Checks]
    E --> F[Target Load]
```

### Business Rules Applied
1. **Customer Deduplication**
   - Match on email, phone, and address
   - Merge duplicate records with most recent data
   - Maintain audit trail of merge decisions

2. **Data Standardization**
   - Normalize address formats
   - Standardize phone number formats
   - Apply consistent naming conventions

3. **Derived Calculations**
   - Customer lifetime value calculation
   - Product recommendation scores
   - Risk assessment indicators

### Error Handling
- **Validation Failures**: Quarantine to error table for manual review
- **Transformation Errors**: Log and retry with exponential backoff
- **Data Quality Issues**: Flag records and continue processing

## Target Systems and Usage

### Consumption Patterns
```yaml
target_systems:
  - system_name: "Data Warehouse"
    purpose: "Analytics and reporting"
    access_pattern: "Batch queries"
    users: "Data analysts, business users"
    
  - system_name: "Real-time API"
    purpose: "Application integration"  
    access_pattern: "High-frequency requests"
    users: "Mobile app, web platform"
    
  - system_name: "ML Platform"
    purpose: "Model training and inference"
    access_pattern: "Batch and streaming"
    users: "Data scientists, ML engineers"
```

### Performance Characteristics
- **Query Response Time**: < 2 seconds for 95% of queries
- **Data Latency**: End-to-end processing < 30 minutes
- **Throughput**: 10,000 requests/second peak capacity
- **Availability**: 99.95% uptime SLA

## Impact Analysis

### Business Dependencies
- **Revenue Impact**: Critical for daily sales reporting
- **Operational Impact**: Powers customer service tools
- **Compliance Impact**: Required for regulatory reporting
- **Strategic Impact**: Enables business intelligence and planning

### Failure Scenarios
- **Source System Outage**: Graceful degradation with cached data
- **Pipeline Failure**: Automated retry and alert mechanisms  
- **Data Quality Issues**: Quarantine and manual review processes
- **Target System Issues**: Circuit breaker and failover procedures

### Change Management
- **Schema Changes**: Backward compatibility requirements
- **Business Logic Updates**: Staged deployment with validation
- **Performance Optimization**: Load testing and gradual rollout
- **Disaster Recovery**: RTO < 4 hours, RPO < 1 hour

## Technical Specifications

### Infrastructure Requirements
- **Compute**: Auto-scaling container orchestration
- **Storage**: Distributed file system with replication
- **Network**: High-bandwidth, low-latency connections
- **Monitoring**: Comprehensive observability stack

### Security and Compliance
- **Data Encryption**: At rest and in transit
- **Access Controls**: Role-based with MFA
- **Audit Logging**: Complete trail of data access and changes
- **Privacy Controls**: PII masking and anonymization

## Operational Procedures

### Monitoring and Alerting
- **Data Quality Metrics**: Automated scorecards and alerts
- **Performance Monitoring**: SLA tracking and capacity planning
- **Error Detection**: Real-time alerting and escalation
- **Business Metrics**: Key performance indicators dashboard

### Maintenance Procedures
- **Regular Updates**: Monthly deployment windows
- **Capacity Planning**: Quarterly growth projections
- **Disaster Recovery**: Annual DR testing
- **Security Reviews**: Bi-annual security assessments

### Documentation Standards
- **Version Control**: All changes tracked in Git
- **Change Logs**: Detailed impact and rollback procedures
- **Runbooks**: Step-by-step operational procedures
- **Training Materials**: User guides and best practices
"""
    }
    
    template_content = templates.get(template_type.lower())
    if not template_content:
        available_types = list(templates.keys())
        return {
            "text": f"Template type '{template_type}' not found. Available types: {', '.join(available_types)}"
        }
    
    return {"text": template_content}


async def quality_assessment_template_resource(
    assessment_type: str = "comprehensive",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Provide templates for data quality assessments.
    
    Args:
        assessment_type: Type of assessment (comprehensive, quick, targeted)
        ctx: FastMCP context for logging
        
    Returns:
        Dictionary containing assessment template
    """
    
    if ctx:
        await ctx.info(f"Loading {assessment_type} quality assessment template")
    
    templates = {
        "comprehensive": """# Comprehensive Data Quality Assessment

## Assessment Overview
- **Assessment Type**: Comprehensive 360-degree review
- **Duration**: 4-6 weeks
- **Scope**: All critical data assets and processes
- **Resources Required**: Data team, business stakeholders, IT support

## Phase 1: Data Discovery and Inventory (Week 1)

### Objectives:
- Catalog all data assets in scope
- Identify data owners and stewards
- Map data flows and dependencies
- Classify data by business importance

### Activities:
1. **Asset Inventory**
   - Database and table discovery
   - File system and object storage scan
   - API and service endpoint mapping
   - Documentation review and collection

2. **Stakeholder Interviews**
   - Business data owners
   - Technical data stewards
   - Data consumers and analysts
   - Compliance and risk teams

3. **Data Flow Mapping**
   - Source system identification
   - Transformation process documentation
   - Target system and usage analysis
   - Integration point discovery

### Deliverables:
- Comprehensive data inventory spreadsheet
- Data flow diagrams and documentation
- Stakeholder contact matrix
- Initial risk assessment

## Phase 2: Quality Baseline Assessment (Week 2-3)

### Data Profiling Activities:
1. **Structural Analysis**
   - Schema validation and consistency
   - Data type and format analysis
   - Constraint and relationship validation
   - Null value and completeness analysis

2. **Content Analysis**
   - Value distribution and patterns
   - Outlier and anomaly detection
   - Duplicate record identification
   - Referential integrity validation

3. **Business Rule Validation**
   - Compliance with business logic
   - Cross-system consistency checks
   - Historical trend analysis
   - Exception pattern identification

### Quality Dimensions Measured:
- **Completeness**: 95% target for critical fields
- **Accuracy**: <2% error rate target
- **Consistency**: 98% cross-system match rate
- **Timeliness**: <1 day latency for critical data
- **Validity**: 100% compliance with business rules

## Phase 3: Impact Analysis and Prioritization (Week 4)

### Business Impact Assessment:
1. **Revenue Impact**
   - Customer-facing data accuracy
   - Billing and financial reporting
   - Sales pipeline and forecasting
   - Product recommendation quality

2. **Operational Impact**
   - Process efficiency and automation
   - Decision-making speed and quality
   - Customer service effectiveness
   - Regulatory compliance readiness

3. **Risk Assessment**
   - Data breach and privacy risks
   - Regulatory non-compliance exposure
   - Reputational damage potential
   - Financial loss scenarios

### Prioritization Framework:
| Priority | Criteria | Action Required |
|----------|----------|-----------------|
| Critical | High business impact + Poor quality | Immediate remediation |
| High     | High business impact + Medium quality | Planned improvement |
| Medium   | Medium business impact + Poor quality | Targeted fixes |
| Low      | Low business impact + Any quality | Monitor and review |

## Phase 4: Recommendations and Roadmap (Week 5-6)

### Improvement Recommendations:
1. **Quick Wins (0-3 months)**
   - Data validation rule implementation
   - Automated quality monitoring setup
   - Basic data cleansing procedures
   - Alert and notification systems

2. **Medium-term Improvements (3-12 months)**
   - Advanced data profiling tools
   - Data governance framework
   - Quality metrics dashboard
   - Master data management

3. **Long-term Initiatives (1-2 years)**
   - Enterprise data platform
   - Machine learning quality detection
   - Real-time data validation
   - Advanced analytics capabilities

### Success Metrics:
- Quality score improvement targets
- Incident reduction percentages
- User satisfaction improvements
- Business value realization
""",

        "quick": """# Quick Data Quality Assessment

## 1-Week Rapid Assessment Framework

### Day 1-2: Data Discovery
- Identify top 10 critical datasets
- Interview key data stakeholders
- Document basic data flows
- Assess current monitoring capabilities

### Day 3-4: Quality Sampling
- Profile representative data samples
- Run basic quality checks
- Identify obvious data issues
- Document quality patterns

### Day 5: Analysis and Recommendations
- Prioritize critical quality issues
- Develop immediate action plan
- Estimate improvement effort
- Present findings to stakeholders

## Key Quality Checks:
1. **Null/Missing Values**: Percentage by field
2. **Data Freshness**: Last update timestamps
3. **Format Consistency**: Pattern analysis
4. **Obvious Outliers**: Statistical anomalies
5. **Duplicate Records**: Exact and fuzzy matches

## Rapid Assessment Tools:
- SQL queries for basic profiling
- Excel/Google Sheets for analysis
- Simple visualization tools
- Automated data quality tools (if available)

## Expected Outcomes:
- High-level quality scorecard
- Top 5 critical issues identified
- 30-60-90 day improvement plan
- Resource requirements estimate
""",

        "targeted": """# Targeted Data Quality Assessment

## Focus Area Deep Dive

### Assessment Scope:
- Specific dataset or business process
- Particular quality dimension (completeness, accuracy, etc.)
- Known problem areas requiring investigation
- Compliance or regulatory requirement

### Methodology:
1. **Problem Definition**
   - Specific quality issues to investigate
   - Business impact and urgency
   - Success criteria and targets
   - Stakeholder expectations

2. **Detailed Analysis**
   - Root cause investigation
   - Data lineage analysis
   - Process flow examination
   - System and tool evaluation

3. **Solution Design**
   - Targeted remediation approach
   - Tool and technology recommendations
   - Process improvement suggestions
   - Monitoring and control measures

### Common Targeted Assessments:
- **Customer Data Accuracy**: Address validation, contact information
- **Financial Data Completeness**: Revenue recognition, transaction details
- **Regulatory Compliance**: GDPR, CCPA, SOX data requirements
- **Master Data Consistency**: Product catalogs, customer hierarchies
- **Real-time Data Timeliness**: Streaming data, API responses

## Deliverables:
- Focused analysis report
- Specific remediation plan
- Implementation timeline
- Monitoring recommendations
"""
    }
    
    template_content = templates.get(assessment_type.lower())
    if not template_content:
        available_types = list(templates.keys())
        return {
            "text": f"Assessment type '{assessment_type}' not found. Available types: {', '.join(available_types)}"
        }
    
    return {"text": template_content}


async def lineage_documentation_template_resource(
    documentation_level: str = "standard",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Provide templates for data lineage documentation.
    
    Args:
        documentation_level: Level of detail (basic, standard, comprehensive)
        ctx: FastMCP context for logging
        
    Returns:
        Dictionary containing lineage documentation template
    """
    
    if ctx:
        await ctx.info(f"Loading {documentation_level} lineage documentation template")
    
    templates = {
        "basic": """# Basic Data Lineage Documentation

## Asset Information
- **Asset Name**: [Name]
- **Asset Type**: [Table/View/Dataset]
- **Business Purpose**: [Brief description]
- **Owner**: [Business owner name]

## Source Information
- **Source System**: [System name]
- **Source Location**: [Database/schema/table]
- **Update Frequency**: [Real-time/Daily/Weekly]
- **Data Volume**: [Approximate size]

## Target Information  
- **Target System**: [System name]
- **Target Location**: [Database/schema/table]
- **Usage Purpose**: [Analytics/Reporting/Operations]
- **Consumers**: [Who uses this data]

## Simple Flow Diagram
```
[Source] → [Transformation] → [Target]
```

## Key Transformations
- [List main transformations applied]

## Contact Information
- **Technical Contact**: [Name/email]
- **Business Contact**: [Name/email]
""",

        "standard": """# Standard Data Lineage Documentation

## Executive Summary
- **Asset Name**: [Full qualified name]
- **Business Domain**: [Finance/Sales/Marketing/etc.]
- **Criticality**: [High/Medium/Low]
- **Last Updated**: [Date]

## Asset Details
- **Type**: [Table/View/Dataset/File]
- **Location**: [Full path/connection]
- **Schema**: [Brief schema description]
- **Size**: [Row count/file size]
- **Growth Rate**: [Growth pattern]

## Data Sources
| Source System | Connection Type | Update Frequency | Data Volume | Quality Score |
|---------------|----------------|------------------|-------------|---------------|
| CRM System    | API            | Real-time        | 1M records  | 95%           |
| ERP System    | Database       | Daily            | 500K records| 92%           |

## Transformation Process
1. **Data Extraction**
   - Source connection details
   - Extraction method and schedule
   - Error handling procedures

2. **Data Validation**
   - Quality checks performed
   - Business rule validation
   - Exception handling

3. **Data Transformation**
   - Cleaning and standardization
   - Business logic application
   - Derived field calculations

4. **Data Loading**
   - Target system details
   - Loading strategy and schedule
   - Success/failure handling

## Data Flow Diagram
```mermaid
graph TD
    A[Source System] -->|Extract| B[Staging Area]
    B -->|Transform| C[Processing Engine]
    C -->|Load| D[Target System]
    C -->|Quality Check| E[Quality Dashboard]
```

## Dependencies
- **Upstream Systems**: [List systems this depends on]
- **Downstream Systems**: [List systems that depend on this]
- **External Dependencies**: [Third-party services, APIs]

## Quality & Monitoring
- **Quality Metrics**: [Key quality indicators]
- **Monitoring**: [What is monitored and how]
- **Alerts**: [Alert conditions and recipients]
- **SLAs**: [Service level agreements]

## Change Management
- **Change Process**: [How changes are managed]
- **Testing**: [Testing procedures]
- **Deployment**: [Deployment process]
- **Rollback**: [Rollback procedures]
""",

        "comprehensive": """# Comprehensive Data Lineage Documentation

## 1. Executive Summary

### Business Context
- **Asset Name**: [Full qualified name with aliases]
- **Business Domain**: [Primary business area]
- **Strategic Importance**: [Critical/Important/Standard]
- **Business Purpose**: [Detailed business use case]
- **Stakeholder Impact**: [Who is affected and how]

### Technical Overview
- **Asset Type**: [Table/View/Dataset/File/Stream]
- **Technology Stack**: [Databases, tools, platforms used]
- **Architecture Pattern**: [Batch/Streaming/Hybrid/Event-driven]
- **Last Major Update**: [Date and nature of change]

## 2. Detailed Asset Information

### Physical Characteristics
```yaml
asset_details:
  qualified_name: "database.schema.table_name"
  asset_type: "Table"
  location: "s3://bucket/path/to/data"
  file_format: "Parquet"
  compression: "GZIP"
  partitioning: "date_partition YYYY-MM-DD"
  
size_metrics:
  current_size_gb: 2500
  row_count: 1.2e9
  daily_growth_gb: 15
  retention_period: "7 years"
  
schema_info:
  total_columns: 45
  nullable_columns: 12
  indexed_columns: 8
  primary_key: ["customer_id", "transaction_date"]
```

### Data Governance
- **Classification**: [Public/Internal/Confidential/Restricted]
- **Compliance Requirements**: [GDPR/CCPA/SOX/etc.]
- **Data Retention**: [Policy and implementation]
- **Privacy Controls**: [PII handling, masking rules]

## 3. Source Systems Analysis

### Primary Sources
```yaml
source_systems:
  - name: "Customer CRM (Salesforce)"
    connection_type: "REST API"
    extraction_method: "Incremental with change tracking"
    schedule: "Every 15 minutes"
    data_volume: "~50K records/hour"
    reliability: "99.9% uptime"
    contact: "crm-team@company.com"
    
  - name: "Transaction Database (PostgreSQL)"
    connection_type: "Database Direct"
    extraction_method: "CDC (Change Data Capture)"
    schedule: "Real-time streaming"
    data_volume: "~10K transactions/minute"
    reliability: "99.95% uptime"
    contact: "db-team@company.com"
```

### Source Data Quality
| Source | Completeness | Accuracy | Consistency | Timeliness | Overall Score |
|--------|-------------|----------|-------------|------------|---------------|
| CRM System | 96% | 94% | 98% | 99% | 97% |
| Transaction DB | 99% | 98% | 99% | 100% | 99% |

## 4. Transformation Pipeline

### Pipeline Architecture
```mermaid
graph TB
    subgraph "Source Layer"
        S1[CRM System]
        S2[Transaction DB]
        S3[External API]
    end
    
    subgraph "Ingestion Layer"
        I1[API Gateway]
        I2[CDC Processor]
        I3[Batch Loader]
    end
    
    subgraph "Processing Layer"
        P1[Data Validation]
        P2[Business Rules]
        P3[Enrichment]
        P4[Quality Checks]
    end
    
    subgraph "Storage Layer"
        T1[Data Warehouse]
        T2[Data Lake]
        T3[Cache Layer]
    end
    
    S1 --> I1
    S2 --> I2
    S3 --> I3
    I1 --> P1
    I2 --> P1
    I3 --> P1
    P1 --> P2
    P2 --> P3
    P3 --> P4
    P4 --> T1
    P4 --> T2
    P4 --> T3
```

### Detailed Transformation Logic
1. **Stage 1: Data Ingestion**
   ```sql
   -- Example transformation rule
   SELECT 
       customer_id,
       UPPER(TRIM(customer_name)) as customer_name,
       REGEXP_REPLACE(phone, '[^0-9]', '') as phone_cleaned,
       CURRENT_TIMESTAMP as ingestion_timestamp
   FROM raw_customer_data
   WHERE customer_id IS NOT NULL
   ```

2. **Stage 2: Business Rule Application**
   - Customer deduplication logic
   - Data standardization rules
   - Derived field calculations
   - Validation rule enforcement

3. **Stage 3: Quality Enrichment**
   - Address standardization
   - Email validation
   - Phone number formatting
   - Reference data lookups

### Error Handling & Recovery
- **Validation Failures**: Route to quarantine table for manual review
- **Transformation Errors**: Retry with exponential backoff, max 3 attempts
- **System Failures**: Automatic failover to backup processing cluster
- **Data Quality Issues**: Flag records, continue processing, generate alerts

## 5. Target Systems & Consumption

### Target System Details
```yaml
target_systems:
  - name: "Enterprise Data Warehouse"
    technology: "Snowflake"
    purpose: "Analytics and BI reporting"
    update_frequency: "Near real-time (< 5 min)"
    users: "Analysts, executives, automated reports"
    access_pattern: "Complex analytical queries"
    
  - name: "Customer 360 API"
    technology: "Redis + PostgreSQL"
    purpose: "Real-time customer service"
    update_frequency: "Real-time streaming"
    users: "Customer service reps, mobile apps"
    access_pattern: "High-frequency point lookups"
    
  - name: "ML Feature Store"
    technology: "Feature Store (Feast)"
    purpose: "Machine learning model training/serving"
    update_frequency: "Batch daily + streaming"
    users: "Data scientists, ML models"
    access_pattern: "Batch training + online serving"
```

### Performance Characteristics
| Target System | Avg Response Time | Peak Throughput | Availability SLA |
|---------------|------------------|-----------------|------------------|
| Data Warehouse | < 2 sec | 1000 queries/sec | 99.9% |
| Customer API | < 100 ms | 10K requests/sec | 99.95% |
| ML Feature Store | < 50 ms | 5K features/sec | 99.9% |

## 6. Impact Analysis & Dependencies

### Business Impact Assessment
- **Revenue Impact**: Powers $50M+ in monthly revenue decisions
- **Customer Experience**: Affects 2M+ customer interactions daily
- **Compliance Impact**: Critical for regulatory reporting and audits
- **Operational Impact**: Enables real-time customer service and support

### Dependency Mapping
```yaml
dependencies:
  upstream_critical:
    - "Customer master data service"
    - "Transaction processing system"
    - "Payment gateway integration"
    
  downstream_critical:
    - "Executive dashboard and KPIs"
    - "Customer service application"
    - "Fraud detection ML models"
    - "Regulatory reporting pipeline"
    
  external_dependencies:
    - "Address validation service (SmartyStreets)"
    - "Email validation service (ZeroBounce)"
    - "Credit scoring API (Experian)"
```

### Failure Impact Analysis
| Failure Scenario | Business Impact | Recovery Time | Mitigation Strategy |
|-------------------|-----------------|---------------|-------------------|
| Source system outage | High - Customer service degraded | 2-4 hours | Cached data fallback |
| Pipeline failure | Medium - Delayed analytics | 1-2 hours | Automated retry + alerts |
| Target system failure | High - Real-time services down | 15-30 minutes | Load balancer failover |

## 7. Operational Procedures

### Monitoring & Alerting
```yaml
monitoring:
  data_quality:
    - metric: "Record completeness percentage"
      threshold: "> 95%"
      alert_severity: "Warning"
      
    - metric: "Processing latency"
      threshold: "< 5 minutes end-to-end"
      alert_severity: "Critical"
      
  system_health:
    - metric: "Pipeline success rate"
      threshold: "> 99%"
      alert_severity: "Warning"
      
    - metric: "Source system availability"
      threshold: "> 99.5%"
      alert_severity: "Critical"
```

### Standard Operating Procedures
1. **Daily Health Checks**
   - Review overnight processing logs
   - Validate data quality metrics
   - Check system performance indicators
   - Verify downstream system health

2. **Weekly Maintenance**
   - Performance optimization review
   - Capacity planning assessment
   - Security patch evaluation
   - Documentation updates

3. **Monthly Reviews**
   - Business KPI analysis
   - Cost optimization opportunities
   - Technology roadmap alignment
   - Stakeholder feedback collection

### Change Management Process
1. **Change Request** → 2. **Impact Assessment** → 3. **Testing** → 4. **Approval** → 5. **Deployment** → 6. **Validation**

### Incident Response
- **Severity 1 (Critical)**: 15-minute response, 2-hour resolution target
- **Severity 2 (High)**: 1-hour response, 8-hour resolution target  
- **Severity 3 (Medium)**: 4-hour response, 24-hour resolution target
- **Severity 4 (Low)**: 1-day response, 1-week resolution target

## 8. Security & Compliance

### Data Security Measures
- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Access Control**: Role-based with MFA requirement
- **Network Security**: VPC isolation with private subnets
- **Audit Logging**: Complete access and change audit trail

### Compliance Framework
- **GDPR Compliance**: Data subject rights, consent management
- **CCPA Compliance**: Consumer privacy rights, data transparency
- **SOX Compliance**: Financial data controls, change management
- **Industry Standards**: ISO 27001, SOC 2 Type II

## 9. Performance & Optimization

### Current Performance Metrics
- **End-to-End Latency**: 3.2 minutes average
- **Throughput**: 50K records/second peak
- **Error Rate**: 0.02% average
- **Resource Utilization**: 65% average CPU, 70% average memory

### Optimization Opportunities
1. **Query Optimization**: Improve analytical query performance by 30%
2. **Parallel Processing**: Increase throughput by implementing partitioned processing
3. **Caching Strategy**: Reduce API response times with intelligent caching
4. **Resource Scaling**: Auto-scaling based on demand patterns

## 10. Future Roadmap

### Short-term Enhancements (3-6 months)
- Real-time streaming optimization
- Enhanced data quality monitoring
- Additional source system integration
- Performance tuning and optimization

### Medium-term Initiatives (6-18 months)
- Machine learning data quality detection
- Advanced anomaly detection
- Self-healing pipeline capabilities
- Enhanced privacy controls

### Long-term Vision (18+ months)
- Fully automated data operations
- Predictive quality management
- Advanced lineage visualization
- Zero-downtime deployment capabilities
"""
    }
    
    template_content = templates.get(documentation_level.lower())
    if not template_content:
        available_levels = list(templates.keys())
        return {
            "text": f"Documentation level '{documentation_level}' not found. Available levels: {', '.join(available_levels)}"
        }
    
    return {"text": template_content}
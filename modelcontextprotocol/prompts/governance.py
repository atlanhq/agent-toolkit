"""
Data governance and compliance prompts for Atlan assets.
"""

from typing import List, Optional, Dict, Any
from fastmcp import Context


async def compliance_assessment_prompt(
    regulation_type: str,
    asset_types: Optional[List[str]] = None,
    risk_level: str = "medium",
    ctx: Optional[Context] = None
) -> str:
    """
    Generate a compliance assessment prompt for regulatory requirements.
    
    Args:
        regulation_type: Type of regulation (GDPR, CCPA, SOX, etc.)
        asset_types: Specific asset types to assess
        risk_level: Risk assessment level (low, medium, high)
        ctx: FastMCP context for logging
    """
    
    if ctx:
        await ctx.info(f"Generating {regulation_type} compliance assessment prompt")
    
    asset_scope = asset_types or ["All asset types"]
    risk_considerations = {
        "low": "Standard compliance review with basic controls",
        "medium": "Enhanced review with detailed documentation requirements", 
        "high": "Comprehensive audit with strict controls and monitoring"
    }
    
    return f"""# {regulation_type} Compliance Assessment

Conduct a comprehensive compliance assessment for {regulation_type} requirements across the specified data assets.

## Assessment Scope
- **Regulation**: {regulation_type}
- **Asset Types**: {', '.join(asset_scope)}
- **Risk Level**: {risk_level.title()}
- **Assessment Approach**: {risk_considerations.get(risk_level, 'Standard review')}

## Compliance Framework

### 1. Data Inventory and Classification
- Identify all data elements subject to {regulation_type}
- Classify data by sensitivity and regulatory impact
- Map data flows and processing activities
- Document data retention and disposal practices

### 2. Legal Basis and Consent Management
- Verify lawful basis for data processing
- Review consent mechanisms and documentation
- Assess consent withdrawal processes
- Validate purpose limitation compliance

### 3. Technical and Organizational Measures
- Evaluate data protection by design and default
- Review access controls and authentication
- Assess encryption and pseudonymization
- Validate backup and recovery procedures

### 4. Data Subject Rights
- Review processes for handling data subject requests
- Assess response times and accuracy
- Validate identity verification procedures
- Document escalation and exception handling

### 5. Cross-Border Data Transfers
- Identify international data transfers
- Verify adequacy decisions or appropriate safeguards
- Review standard contractual clauses
- Assess binding corporate rules compliance

### 6. Breach Detection and Response
- Evaluate monitoring and detection capabilities
- Review incident response procedures
- Assess notification timelines and processes
- Document lessons learned and improvements

## Risk Assessment Criteria

### High Risk Indicators:
- Processing of special category data
- Large-scale systematic monitoring
- Public area surveillance
- Automated decision-making with legal effects

### Medium Risk Indicators:
- Regular business processing activities
- Employee monitoring systems
- Customer relationship management
- Marketing and analytics activities

### Low Risk Indicators:
- Internal administrative processes
- Public information processing
- Anonymous statistical analysis
- Standard business communications

## Deliverables Required:

### 1. Compliance Scorecard
- Overall compliance rating by requirement
- Gap analysis with specific deficiencies
- Risk heat map with prioritized actions
- Trend analysis and improvement tracking

### 2. Gap Remediation Plan
- Specific non-compliance issues identified
- Recommended corrective actions
- Implementation timelines and responsibilities
- Cost estimates and resource requirements

### 3. Ongoing Monitoring Strategy
- Key performance indicators for compliance
- Regular review and audit schedules
- Automated monitoring and alerting
- Training and awareness programs

### 4. Documentation Package
- Updated privacy policies and notices
- Data processing agreements and contracts
- Technical and organizational measures documentation
- Incident response and breach notification procedures

## Success Criteria:
- Full compliance with {regulation_type} requirements
- Documented evidence of compliance measures
- Effective ongoing monitoring and governance
- Stakeholder awareness and capability building

Please provide specific, actionable recommendations that demonstrate compliance and reduce regulatory risk.
"""


async def policy_recommendation_prompt(
    business_domain: str,
    current_challenges: Optional[List[str]] = None,
    governance_maturity: str = "developing",
    ctx: Optional[Context] = None
) -> str:
    """
    Generate data governance policy recommendations.
    
    Args:
        business_domain: Business domain or department
        current_challenges: List of current governance challenges
        governance_maturity: Current maturity level (basic, developing, advanced)
        ctx: FastMCP context for logging
    """
    
    if ctx:
        await ctx.info(f"Creating policy recommendations for {business_domain}")
    
    challenges_list = current_challenges or [
        "Data quality inconsistencies",
        "Unclear data ownership",
        "Compliance gaps"
    ]
    
    maturity_frameworks = {
        "basic": {
            "focus": "Foundational policies and basic controls",
            "priorities": ["Data classification", "Access controls", "Basic documentation"]
        },
        "developing": {
            "focus": "Structured governance with defined processes",
            "priorities": ["Policy standardization", "Workflow automation", "Performance monitoring"]
        },
        "advanced": {
            "focus": "Strategic optimization and continuous improvement",
            "priorities": ["Advanced analytics", "Predictive governance", "Innovation enablement"]
        }
    }
    
    maturity_info = maturity_frameworks.get(governance_maturity, maturity_frameworks["developing"])
    
    return f"""# Data Governance Policy Recommendations for {business_domain}

Develop comprehensive data governance policies tailored to {business_domain} requirements and organizational maturity.

## Current State Assessment
- **Business Domain**: {business_domain}
- **Governance Maturity**: {governance_maturity.title()}
- **Focus Area**: {maturity_info['focus']}

## Identified Challenges:
{chr(10).join(f"- {challenge}" for challenge in challenges_list)}

## Policy Framework Recommendations

### 1. Data Ownership and Stewardship
- **Data Owner Responsibilities**
  - Business decision-making authority
  - Quality standards definition
  - Access approval processes
  - Compliance accountability

- **Data Steward Responsibilities**
  - Day-to-day data management
  - Quality monitoring and reporting
  - Issue resolution and escalation
  - Documentation maintenance

- **Implementation Guidelines**
  - Clear role definitions and boundaries
  - Escalation procedures and decision matrices
  - Performance metrics and accountability
  - Training and certification requirements

### 2. Data Classification and Handling
- **Classification Scheme**
  - Public: Freely shareable information
  - Internal: Business-sensitive data
  - Confidential: Restricted access data
  - Restricted: Highly sensitive data (PII, PHI)

- **Handling Requirements by Classification**
  - Storage and transmission standards
  - Access control and authentication
  - Retention and disposal procedures
  - Monitoring and audit requirements

### 3. Data Quality Management
- **Quality Standards**
  - Completeness thresholds and measurement
  - Accuracy validation rules
  - Consistency monitoring across systems
  - Timeliness requirements and SLAs

- **Quality Processes**
  - Regular assessment and reporting
  - Issue identification and remediation
  - Root cause analysis and prevention
  - Continuous improvement initiatives

### 4. Access Control and Security
- **Access Management Principles**
  - Least privilege access model
  - Role-based access controls
  - Regular access reviews and recertification
  - Segregation of duties enforcement

- **Security Requirements**
  - Authentication and authorization standards
  - Encryption for data at rest and in transit
  - Network security and monitoring
  - Incident detection and response

### 5. Compliance and Risk Management
- **Regulatory Compliance**
  - Applicable regulation identification
  - Compliance monitoring and reporting
  - Regular assessment and audit
  - Remediation and corrective action

- **Risk Assessment**
  - Data-related risk identification
  - Impact and likelihood evaluation
  - Risk mitigation strategies
  - Ongoing monitoring and review

## Implementation Roadmap

### Phase 1: Foundation (Months 1-3)
Priority areas based on maturity level:
{chr(10).join(f"- {priority}" for priority in maturity_info['priorities'])}

### Phase 2: Enhancement (Months 4-6)
- Process automation and optimization
- Advanced monitoring and analytics
- Stakeholder training and adoption
- Performance measurement and improvement

### Phase 3: Optimization (Months 7-12)
- Continuous improvement programs
- Advanced governance capabilities
- Innovation and emerging technology adoption
- Ecosystem integration and collaboration

## Success Metrics

### Operational Metrics:
- Policy compliance rates
- Data quality improvement
- Access control effectiveness
- Incident reduction

### Business Metrics:
- Decision-making speed and accuracy
- Risk reduction and mitigation
- Regulatory compliance scores
- Stakeholder satisfaction

## Change Management Strategy

### Communication and Training:
- Executive sponsorship and messaging
- Role-based training programs
- Documentation and knowledge sharing
- Regular feedback and improvement

### Technology Enablement:
- Tool selection and implementation
- Integration with existing systems
- Automation and workflow optimization
- Performance monitoring and analytics

Please provide specific, implementable policies that align with organizational capabilities and business objectives while addressing the identified challenges.
"""
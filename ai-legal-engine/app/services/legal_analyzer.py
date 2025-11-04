"""
Legal Analyzer Service
Performs comprehensive NDPR/NDPA compliance analysis using AI
"""

import json
import re
from typing import List, Tuple, Dict, Optional, Any
import logging
import os
from typing import Dict, Any

from app.services.gemini_service_v2 import get_gemini_service
from app.models.schemas import (
    RiskLevel, ComplianceGap, ComplianceFix, 
    LegalReference, PolicyAnalysisRequest
)
from app.core.config import settings
from app.core.exceptions import AIServiceError, ValidationError

logger = logging.getLogger(__name__)


class LegalAnalyzer:
    """Analyzes legal compliance using AI with platinum-standard NDPR/NDPA framework"""
    
    def __init__(self):
        self.gemini = get_gemini_service()
        self.ndpr_knowledge = self._load_ndpr_knowledge()
        self.analysis_prompt_template = self._load_analysis_prompt_template()
    
    def _load_ndpr_knowledge(self) -> str:
        """Load NDPR/NDPA full text for reference"""
        file_path = os.path.join("app", "data", "ndpr_full_text.txt")
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    logger.info(f"✅ Loaded NDPR knowledge ({len(content)} characters)")
                    return content
            else:
                logger.warning(f"⚠️ NDPR file not found at {file_path}, using fallback")
                return self._get_fallback_ndpr()
        except Exception as e:
            logger.error(f"❌ Failed to load NDPR file: {e}")
            return self._get_fallback_ndpr()
    
    def _get_fallback_ndpr(self) -> str:
        """Comprehensive fallback NDPR/NDPA knowledge base"""
        return """
        ═══════════════════════════════════════════════════════════════
        NIGERIA DATA PROTECTION ACT (NDPA) 2023 - KEY PROVISIONS
        ═══════════════════════════════════════════════════════════════
        
        PART I: FOUNDATIONAL PRINCIPLES (Section 24)
        
        1. Lawfulness, Fairness & Transparency (S. 24(1)(a))
           - Processing must have lawful basis: Consent, Contract, Legal Obligation, 
             Vital Interest, Public Interest, or Legitimate Interest
           - Consent must be: Freely given, Specific, Informed, Unambiguous, Revocable
        
        2. Purpose Limitation (S. 24(1)(b))
           - Data collected for specified, explicit, legitimate purposes only
           - No further processing incompatible with original purpose
        
        3. Data Minimization (S. 24(1)(c))
           - Data must be adequate, relevant, limited to necessity
        
        4. Storage Limitation (S. 24(1)(d))
           - Data retained no longer than necessary for purpose
           - Clear retention periods required
        
        5. Accuracy (S. 24(1)(e))
           - Reasonable steps to ensure data accuracy
           - Inaccurate data must be rectified or erased
        
        6. Integrity & Confidentiality (S. 24(1)(f))
           - Appropriate technical and organizational measures (TOMs)
           - Protection against unauthorized/unlawful processing
        
        7. Accountability (S. 24(1)(g))
           - Controller must demonstrate compliance
           - Documentation and records required
        
        PART II: DATA SUBJECT RIGHTS (Sections 34-39)
        
        1. Right to Information (S. 34)
           - Identity and contact of controller
           - DPO contact details (MANDATORY)
           - Purposes and legal basis for processing
           - Recipients of data
           - Retention periods
           - All rights enumerated
        
        2. Right of Access (S. 35)
           - Confirmation of processing
           - Copy of data
           - Response within 30 days maximum
        
        3. Right to Rectification (S. 36)
           - Correction of inaccurate data
           - Completion of incomplete data
        
        4. Right to Erasure/Right to be Forgotten (S. 37)
           - Deletion when: Consent withdrawn, unlawful processing, 
             no longer necessary, legal obligation
        
        5. Right to Restriction (S. 38)
           - Restriction during accuracy verification
           - For legal claims establishment
        
        6. Right to Data Portability (S. 35(3))
           - Structured, machine-readable format
           - Direct transmission where feasible
        
        7. Right to Object (S. 39)
           - Absolute right for direct marketing
           - Conditional right for legitimate interest processing
        
        8. Right Not to be Subject to Automated Decision-Making (S. 39(4))
           - Prohibition on solely automated decisions with legal effects
           - Right to human intervention
        
        PART III: CONTROLLER OBLIGATIONS
        
        1. Data Protection Officer (S. 5-6)
           - MANDATORY appointment for all controllers
           - Expert knowledge required
           - Independence guaranteed
           - Contact details must be published
        
        2. Data Protection Impact Assessment (S. 33)
           - Required for high-risk processing
           - Must assess: Processing description, necessity, risks, mitigation
        
        3. Security of Processing (S. 31-32)
           - Encryption, pseudonymization where appropriate
           - Regular testing and evaluation
        
        4. Records of Processing Activities (S. 47)
           - Written records maintained
           - Available to NDPC on request
        
        5. Data Breach Notification (S. 40-41)
           - To NDPC: Within 72 hours (if risk exists)
           - To Data Subjects: Without undue delay (if high risk)
        
        PART IV: SPECIAL CATEGORIES
        
        1. Special Category Data (S. 27)
           - Sensitive data: Race, politics, religion, health, biometrics, 
             sex life, criminal convictions
           - Requires explicit consent or specific legal basis
        
        2. Children's Data (S. 26(9) & S. 28)
           - Child: Under 18 years
           - Parental consent required
           - Age verification efforts mandatory
           - Best interests paramount
        
        3. Cross-Border Transfers (S. 43-46)
           - Adequate protection required
           - Mechanisms: Adequacy decision, Standard Clauses, BCRs, Consent
        
        PART V: PENALTIES (S. 65-71)
        
        - Non-compliance fines: Up to 2% annual turnover or NGN 10,000,000
        - Serious violations: Up to 4% annual turnover or NGN 25,000,000
        - Criminal liability for data controllers/processors
        - Civil claims by data subjects for damages
        
        ═══════════════════════════════════════════════════════════════
        """
    
    def _load_analysis_prompt_template(self) -> str:
        """Load or create the comprehensive analysis prompt template"""
        prompt_path = os.path.join("app", "data", "prompts", "ndpa_analysis_prompt.txt")
        
        try:
            if os.path.exists(prompt_path):
                with open(prompt_path, "r", encoding="utf-8") as f:
                    return f.read()
        except Exception as e:
            logger.warning(f"Could not load prompt file: {e}, using built-in template")
        
        return self._get_comprehensive_prompt_template()
    
    def _get_comprehensive_prompt_template(self) -> str:
        """Get the platinum-standard comprehensive analysis prompt"""
        return """
You are Nigeria's foremost data protection legal expert with deep expertise in NDPR/NDPA compliance, constitutional law, sector-specific regulations, and international data protection frameworks. You are recognized for delivering 'platinum standard' forensic legal analysis that anticipates enforcement trends and regulatory interpretations.

TASK: Conduct an exhaustive, multi-layered compliance forensic analysis of this privacy policy for ALL conceivable NDPR/NDPA violations, regulatory gaps, constitutional conflicts, sector-specific non-compliance, and international best-practice deviations across all use case scenarios.

COMPANY: {company_name}
INDUSTRY: {industry}
DOCUMENT TYPE: {document_type}
COMPANY SIZE: {company_size}
TARGET USERS: {target_users}
PROCESSING SCOPE: {processing_scope}

POLICY TEXT (Full Document):
{document_text}

═══════════════════════════════════════════════════════════════
PART A: PRIMARY LEGAL FRAMEWORK (NDPA 2023 - Comprehensive)
═══════════════════════════════════════════════════════════════

**1. FOUNDATIONAL PRINCIPLES (NDPA Section 24)**

1.1 **Lawfulness, Fairness & Transparency (S. 24(1)(a))**
    * **Legal Basis Articulation (S. 25):** Must explicitly state ONE of six lawful bases for EACH processing activity:
      - Consent (S. 26): Freely given, specific, informed, unambiguous, revocable
      - Contract Performance (S. 25(1)(b)): Necessary for contract execution
      - Legal Obligation (S. 25(1)(c)): Required by Nigerian law
      - Vital Interest (S. 25(1)(d)): Life-or-death situations
      - Public Interest (S. 25(1)(e)): Official authority or public task
      - Legitimate Interest (S. 25(1)(f)): Controller's interests not overridden by data subject rights
    
    * **Consent Standards (S. 26):**
      - Must be distinguishable, intelligible, easily accessible
      - Clear affirmative action required (no pre-ticked boxes)
      - Separate consent for different purposes
      - Easy withdrawal mechanism (as easy as giving consent)
      - Burden of proof on controller
      - Special consent for sensitive data (explicit consent required)
    
    * **Transparency Requirements:**
      - Identity and contact details of controller
      - Contact details of Data Protection Officer (DPO) - MANDATORY
      - Purposes and legal basis for each purpose
      - Recipients or categories of recipients
      - International transfer details and safeguards
      - Retention periods or determination criteria
      - All data subject rights enumerated
      - Right to lodge complaint with NDPC
      - Source of data if not collected from subject
      - Automated decision-making existence and logic

1.2 **Purpose Limitation (S. 24(1)(b))**
    * Purposes must be: Specified, Explicit, Legitimate
    * Further processing compatibility test required
    * Purpose creep prohibition
    * Marketing purposes must be explicitly separated

1.3 **Data Minimization (S. 24(1)(c))**
    * Adequacy test: Is data sufficient for purpose?
    * Relevance test: Is data related to purpose?
    * Necessity test: Is each data point essential?
    * Excessive data collection prohibition

1.4 **Accuracy (S. 24(1)(e))**
    * Reasonable steps to ensure accuracy
    * Mechanisms for data subjects to update information
    * Inaccurate data rectification or erasure procedures

1.5 **Storage Limitation (S. 24(1)(d))**
    * Maximum retention periods defined per purpose
    * Justification for extended retention
    * Automatic deletion protocols
    * Archive procedures for legal/public interest retention

1.6 **Integrity & Confidentiality (S. 24(1)(f))**
    * Technical and Organizational Measures (TOMs)
    * Protection against unauthorized processing
    * Accidental loss, destruction, or damage prevention
    * Regular security testing and updates

1.7 **Accountability (S. 24(1)(g))**
    * Controller responsibility for demonstrating compliance
    * Documentation requirements
    * Records of Processing Activities (ROPA) - S. 47
    * Compliance evidence maintenance

**2. DATA SUBJECT RIGHTS (NDPA Sections 34-39) - CRITICAL**

2.1 **Right to Information (S. 34)**
    * At point of collection: All transparency information
    * Clear, concise, transparent language
    * Layered notice acceptable for complex processing

2.2 **Right of Access (S. 35)**
    * Confirmation of processing
    * Copy of data undergoing processing
    * Information about processing (purposes, categories, recipients)
    * Response timeline: Without undue delay, maximum 30 days
    * Free of charge (first request)

2.3 **Right to Rectification (S. 36)**
    * Correction of inaccurate data
    * Completion of incomplete data
    * Supplementary statement mechanism
    * Notification to recipients required

2.4 **Right to Erasure/Right to be Forgotten (S. 37)**
    * Grounds: Consent withdrawal, unlawful processing, legal obligation, no longer necessary
    * Exceptions: Legal claims, freedom of expression, legal obligations
    * Third-party notification if data disclosed
    * Specific procedures for public data

2.5 **Right to Restriction of Processing (S. 38)**
    * Accuracy contested period
    * Unlawful processing objection
    * Data no longer needed but subject needs for legal claims
    * Legitimate grounds verification pending

2.6 **Right to Data Portability (S. 35(3))**
    * Structured, commonly used, machine-readable format
    * Direct transmission to another controller where feasible
    * Only for automated consent-based or contract-based processing

2.7 **Right to Object (S. 39)**
    * Absolute right for direct marketing (including profiling)
    * Conditional right for legitimate interest processing
    * Absolute right for research/statistics (unless public interest)
    * Override test: Controller's compelling grounds vs. data subject interests

2.8 **Right Not to be Subject to Automated Decision-Making (S. 39(4))**
    * Prohibition on solely automated decisions with legal/significant effects
    * Exceptions: Necessary for contract, authorized by law, explicit consent
    * Right to human intervention, express views, contest decision
    * Special protection for children and vulnerable persons

**3. CONTROLLER & PROCESSOR OBLIGATIONS**

3.1 **Data Protection Officer (DPO) Requirements (S. 5-6)**
    * MANDATORY appointment for all controllers and processors
    * DPO designation to be communicated to NDPC
    * Required qualifications: Expert knowledge of data protection law
    * Independence requirements
    * Resources and access rights
    * Contact details must be published
    * Tasks: Monitor compliance, advise, cooperate with NDPC, contact point

3.2 **Data Protection Impact Assessment (DPIA) - S. 33**
    * Required for high-risk processing, including:
      - Systematic automated processing with legal effects
      - Large-scale special category data processing
      - Systematic public area monitoring
      - New technologies with high privacy risk
    * DPIA must contain: Processing description, necessity assessment, risks assessment, mitigation measures
    * Prior consultation with NDPC if high residual risk

3.3 **Security of Processing (S. 31-32)**
    * Risk-appropriate technical measures: Pseudonymization, encryption
    * Organizational measures: Staff training, access controls, policies
    * Regular testing and evaluation
    * Processor security obligations identical
    * Supply chain security verification

3.4 **Records of Processing Activities (S. 47)**
    * Written records maintained by controllers and processors
    * Contents: Controller/processor details, purposes, categories, recipients, transfers, retention, security measures
    * Available to NDPC on request

3.5 **Data Breach Notification (S. 40-41)**
    * **To NDPC:** Within 72 hours of awareness (if risk to rights/freedoms)
    * **To Data Subjects:** Without undue delay (if high risk)
    * Breach register maintenance required
    * Documentation: Facts, effects, remedial action
    * Penalties for non-notification

**4. SPECIAL CATEGORY DATA (S. 27 - SENSITIVE DATA)**
    * Definition: Racial/ethnic origin, political opinions, religious beliefs, trade union membership, genetic data, biometric data, health data, sex life, sexual orientation, criminal convictions
    * Processing prohibition unless:
      - Explicit consent for specific purposes
      - Legal obligation (employment, social security)
      - Vital interests (data subject unable to consent)
      - Legitimate activities (foundations, associations, religious bodies)
      - Data manifestly made public by subject
      - Legal claims or judicial acts
      - Substantial public interest
      - Preventive/occupational medicine
      - Public health interest
      - Archiving/research/statistics with safeguards

**5. CHILDREN'S DATA (S. 26(9) & S. 28)**
    * Child definition: Under 18 years
    * Parental/guardian consent required
    * Controller must make reasonable efforts to verify
    * Age-appropriate language and design
    * Best interests of child paramount
    * Prohibition on profiling children for marketing
    * Educational context considerations

**6. CROSS-BORDER TRANSFERS (S. 43-46)**
    * Prohibition unless adequate protection ensured
    * **Transfer Mechanisms:**
      - NDPC adequacy decision for destination country
      - Standard Data Protection Clauses (SDPCs)
      - Binding Corporate Rules (BCRs)
      - Explicit informed consent
      - Contract performance necessity
      - Legal claims establishment
      - Vital interests protection
      - Public register transfers
    * Onward transfer restrictions
    * Documentation requirements

═══════════════════════════════════════════════════════════════
PART B: SECONDARY LEGAL FRAMEWORKS
═══════════════════════════════════════════════════════════════

**1. CONSTITUTIONAL & FOUNDATIONAL LAWS**

1.1 **Constitution of the Federal Republic of Nigeria 1999 (As Amended)**
    * S. 37: Right to Privacy (fundamental right)
    * S. 39: Right to Freedom of Expression
    * S. 41: Right to Freedom of Movement
    * Privacy policy must not violate constitutional rights

1.2 **Freedom of Information Act 2011**
    * Intersection with data protection
    * Public body obligations
    * Exemptions for personal data

**2. SECTOR-SPECIFIC REGULATIONS**

2.1 **Financial Services**
    * **CBN Consumer Protection Framework 2016**
    * **Banks and Other Financial Institutions Act (BOFIA) 2020**
    * Requirements: Clear fee disclosures, cooling-off periods, dispute resolution
    
2.2 **Telecommunications**
    * **Nigerian Communications Act 2003**
    * **NCC Subscriber Registration Regulations 2011**
    * **Lawful Intercept Regulations**
    * Requirements: SIM registration data protection, lawful intercept disclosures

2.3 **Healthcare**
    * **National Health Act 2014**
    * Medical records confidentiality (S. 26-27)
    * Patient consent requirements
    * Electronic health records standards

2.4 **Insurance**
    * **Insurance Act 2003**
    * **NAICOM Operational Guidelines**
    * Disclosure requirements for underwriting

2.5 **Education**
    * Student data protection requirements
    * Educational records confidentiality

2.6 **E-Commerce & Online Platforms**
    * **Cybercrimes Act 2015**
    * **Consumer Protection Act 2019**
    * Requirements: Clear pricing, refund policies, contact information

**3. MARKETING & COMMUNICATIONS**

3.1 **Direct Marketing Compliance**
    * Opt-in requirements for electronic marketing
    * Unsubscribe mechanisms (one-click)
    * Suppression list maintenance
    * B2B vs. B2C distinctions
    * SMS/email/call marketing rules

**4. EMPLOYMENT DATA PROCESSING**

4.1 **Labour Act (Chapter L1) LFN 2004**
    * Employee data processing limitations
    * Workplace monitoring disclosure requirements

4.2 **Employee Monitoring**
    * Legitimate interest vs. privacy rights balance
    * Notice requirements for surveillance
    * Proportionality assessments

**5. ANTI-MONEY LAUNDERING (AML) & KYC**

5.1 **Money Laundering (Prevention and Prohibition) Act 2022**
    * KYC data retention (minimum 5 years post-relationship)
    * Conflict resolution with data minimization
    * Legal basis: Legal obligation

═══════════════════════════════════════════════════════════════
PART C: USE CASE SCENARIO TESTING (All 67 Scenarios)
═══════════════════════════════════════════════════════════════

Test the policy against ALL scenarios. Flag ANY inadequate coverage as a compliance gap:

**LIFECYCLE (12):** New user registration (adult), Minor registration (under 18), Guest browsing, Account modification, Account deletion, Data portability, Consent withdrawal, Access request (SAR), Rectification, Erasure with legal holds, Processing restriction, Objection to processing

**SPECIAL CATEGORY DATA (6):** Health data, Biometric data, Political opinions, Religious data, Genetic data, Criminal convictions

**TRANSFERS (6):** International transfers, Third-party providers, Group companies, M&A restructuring, Law enforcement disclosure, Subprocessors

**MARKETING (5):** Direct marketing, Profiling/targeting, Ad networks, Existing customer marketing, Affiliate marketing

**TECHNICAL (8):** Cookies, Automated decisions, AI/ML training, Analytics tracking, Session recording, Chatbots, API sharing, Mobile permissions

**SECURITY (6):** Personal data breach, Sensitive data breach, No-loss incident, Ransomware, Insider threat, Vendor breach

**SPECIAL POPULATIONS (5):** Children under 13, Disabled persons, Non-literate users, Vulnerable adults, Deceased persons

**EMPLOYMENT (5):** HR records, Workplace monitoring, Background checks, Wellness programs, Contractor data

**CROSS-BORDER (4):** Nigerians abroad, Foreigners in Nigeria, Multi-jurisdictional compliance, Government users

**FINANCIAL (4):** Payment cards (PCI-DSS), Credit scoring, KYC/AML, Transaction monitoring

**EDGE CASES (6):** Identity verification failure, Excessive requests, Conflicting legal obligations, Anonymization claims, Research purposes, Public interest vs. privacy

═══════════════════════════════════════════════════════════════
PART D: ANALYSIS METHODOLOGY
═══════════════════════════════════════════════════════════════

1. **Systematic Review:**
   - Map EVERY data processing activity to a lawful basis
   - Verify EVERY data subject right has explicit procedures
   - Test EVERY use case scenario above
   - Check for internal contradictions

2. **Severity Rating:**
   - **CRITICAL (-25 to -40):** Fundamental violations, missing DPO, no breach procedures, unlawful child/sensitive data processing
   - **HIGH (-15 to -25):** Missing data subject rights, inadequate consent, no retention periods, weak security
   - **MEDIUM (-8 to -15):** Partial rights coverage, incomplete transparency, unclear processors
   - **LOW (-2 to -8):** Minor clarity issues, formatting, best practice gaps

3. **Compliance Scoring:**
   - Base: 100 points
   - Deductions per severity
   - Bonuses: ISO certs (+5), Privacy by Design (+5), Audits (+5)
   - **Grades:** 95-120 Platinum, 85-94 Gold, 70-84 Silver, 50-69 Bronze, 30-49 Critical, 0-29 Catastrophic

4. **Impact Assessment (per gap):**
   - Regulatory risk & NDPC penalty exposure
   - Financial risk (2-4% turnover or NGN 10M-25M)
   - Operational risk (processing suspension)
   - Reputational risk
   - Legal risk (civil claims)

5. **Remediation Priority:**
   - IMMEDIATE (0-7 days): CRITICAL gaps
   - URGENT (1-4 weeks): HIGH gaps
   - PRIORITY (1-3 months): MEDIUM gaps
   - PLANNED (3-12 months): LOW gaps

═══════════════════════════════════════════════════════════════
OUTPUT FORMAT (MANDATORY JSON)
═══════════════════════════════════════════════════════════════

{{
  "compliance_score": 0,
  "compliance_grade": "platinum/gold/silver/bronze/critical/catastrophic",
  "risk_level": "critical/high/medium/low",
  "total_gaps": 0,
  "gaps_by_severity": {{"critical": 0, "high": 0, "medium": 0, "low": 0}},
  "gaps": [
    {{
      "gap_id": "gap_001",
      "category": "Lawful Basis / Data Subject Rights / Security / etc",
      "title": "Concise gap title",
      "description": "Detailed description with specific deficiency and legal requirement",
      "severity": "critical/high/medium/low",
      "ndpr_articles": ["S. 25(1)(a)", "S. 24(1)(a)"],
      "secondary_laws": ["Consumer Protection Act 2019 - S. 115"],
      "use_case_scenarios": ["Lifecycle Scenario 2", "Marketing Scenario 25"],
      "impact": {{
        "regulatory": "NDPC enforcement likelihood and penalty range",
        "operational": "Processing impacts",
        "reputational": "Trust and brand impacts",
        "legal": "Civil claim risks",
        "financial": "Estimated NGN exposure range"
      }},
      "affected_data_subjects": "Who is impacted",
      "recommendation": "Prioritized, actionable remediation with timeline",
      "implementation_priority": "immediate/urgent/priority/planned",
      "estimated_effort": "Low/Medium/High (X weeks)",
      "success_criteria": "Measurable compliance indicators"
    }}
  ],
  "fixes": [
    {{
      "gap_id": "gap_001",
      "fix_id": "fix_001",
      "fix_title": "Fix title",
      "fix_type": "policy_update/technical/procedural/training",
      "current_text": "Exact problematic text from policy",
      "suggested_text": "Compliant replacement text with NDPA references",
      "implementation_steps": ["Step 1", "Step 2", "..."],
      "technical_requirements": "Systems/tools needed",
      "documentation_needed": "Required records/docs",
      "effort_level": "low/medium/high",
      "estimated_cost": "NGN X - Y",
      "timeline": "X weeks/months",
      "responsible_party": "Role(s) accountable",
      "verification_method": "How to confirm compliance"
    }}
  ],
  "executive_summary": {{
    "overall_assessment": "Comprehensive narrative",
    "key_strengths": ["Strength 1", "Strength 2"],
    "critical_weaknesses": ["Weakness 1 with risk", "Weakness 2 with risk"],
    "immediate_actions": ["Action 1 (0-7 days)", "Action 2 (0-7 days)"],
    "compliance_roadmap": "Phased plan: Immediate → Urgent → Priority → Planned",
    "estimated_total_remediation_cost": "NGN X - Y million",
    "estimated_compliance_timeline": "X months to full compliance"
  }},
  "legal_references": [
    {{
      "reference_id": "ref_001",
      "regulation": "Nigeria Data Protection Act 2023",
      "article": "Section X",
      "title": "Article title",
      "full_text": "Complete legal text",
      "interpretation": "Legal interpretation",
      "relevance": "Why this matters to gaps found",
      "enforcement_history": "NDPC precedents if known",
      "related_articles": ["S. X", "S. Y"]
    }}
  ],
  "industry_benchmarking": {{
    "industry_average_score": 72,
    "top_performer_score": 94,
    "position": "Above/Below/At average",
    "peer_comparison": "Competitor analysis"
  }},
  "risk_matrix": {{
    "likelihood_of_enforcement": "high/medium/low",
    "severity_of_consequences": "high/medium/low",
    "overall_risk_rating": "critical/high/medium/low",
    "risk_narrative": "Enforcement probability explanation"
  }},
  "certification_readiness": {{
    "iso_27701": "ready/partially_ready/not_ready",
    "privacy_seal": "ready/partially_ready/not_ready",
    "gaps_preventing_certification": ["Gap 1", "Gap 2"]
  }},
  "monitoring_recommendations": [
    "Quarterly reviews",
    "Bi-annual DPIAs",
    "Monthly DSR tracking",
    "Annual audits",
    "Regulatory monitoring"
  ]
}}

═══════════════════════════════════════════════════════════════
QUALITY CHECKLIST
═══════════════════════════════════════════════════════════════

Before finalizing:
✓ All 67 use cases tested
✓ Every NDPA section (24-47) reviewed
✓ Every data subject right (S. 34-39) verified
✓ Sector regulations checked
✓ Every gap has: ID, severity, articles, impact, fix
✓ Every fix has: ID, current text, suggested text, steps
✓ Score calculated accurately
✓ JSON structure valid

═══════════════════════════════════════════════════════════════
CRITICAL REMINDERS
═══════════════════════════════════════════════════════════════

1. **Be Exhaustive:** Find EVERYTHING. This is forensic analysis.
2. **Be Specific:** State EXACTLY what's missing, why it violates which law, precise remedy.
3. **Be Practical:** Actionable steps, timelines, cost estimates for non-lawyers.
4. **Be Current:** Apply 2023 NDPA, not 2019 NDPR.
5. **Be Rigorous:** Test all scenarios. Document verification.
6. **Be Realistic:** Base severity on actual NDPC priorities, not theoretical max.
7. **Be Comprehensive:** Every gap needs fix. Every fix needs steps.

NOW ANALYZE WITH PLATINUM-STANDARD RIGOR.

Return ONLY valid JSON, no other text.
"""
    
    async def analyze_policy(
        self,
        request: PolicyAnalysisRequest
    ) -> Tuple[int, RiskLevel, List[ComplianceGap], List[ComplianceFix], str, List[LegalReference], Dict[str, Any]]:
        """
        Main analysis method - analyzes privacy policy for NDPR/NDPA compliance
        
        Args:
            request: PolicyAnalysisRequest with company and policy details
            
        Returns:
            Tuple of (score, risk_level, gaps, fixes, summary, references, executive_summary_dict)
            
        Raises:
            ValidationError: If input validation fails
            AIServiceError: If AI analysis fails
        """
        logger.info(f"🔍 Starting analysis for {request.company_name}")
        logger.info(f"📄 Policy length: {len(request.document_text)} characters")
        
        try:
            # Validate input
            if not request.document_text or not request.document_text.strip():
                raise ValidationError(
                    "Document text cannot be empty",
                    error_code="EMPTY_DOCUMENT"
                )
            
            # Determine optimal text length based on model capacity
            max_policy_length = 15000
            policy_text = request.document_text[:max_policy_length]
            
            if len(request.document_text) > max_policy_length:
                logger.warning(
                    f"⚠️ Policy truncated from {len(request.document_text)} to {max_policy_length} chars"
                )
            
            # Build comprehensive prompt using dynamic sizing
            prompt = self._get_analysis_prompt(request, policy_text)
            
            logger.info("📤 Sending analysis request to Gemini AI...")
            
            # Use lower temperature for precision analysis
            response = await self.gemini.generate_text(prompt, temperature=0.1)
            
            logger.info(f"📥 Received AI response ({len(response)} characters)")
            
            # Parse JSON response
            analysis = self._parse_json_response(response)
            
            # Extract and validate data
            score = self._extract_compliance_score(analysis)
            risk_level = self._calculate_risk_level(score)
            
            # Process gaps
            gaps = self._process_gaps(analysis.get('gaps', []))
            
            # Generate fixes for identified gaps
            fixes = await self._generate_fixes(gaps, request.document_text)
            
            # Extract summaries
            summary = analysis.get('summary', self._generate_default_summary(score, len(gaps)))
            
            # Ensure executive_summary is always a dict for consistency
            executive_summary_dict = analysis.get('executive_summary', {})
            if isinstance(executive_summary_dict, str):
                executive_summary_dict = {"overall_assessment": executive_summary_dict}
            elif not isinstance(executive_summary_dict, dict):
                executive_summary_dict = {}
            
            # Create legal references
            references = self._create_legal_references(gaps, analysis.get('legal_references', []))
            
            logger.info(
                f"✅ Analysis complete: Score={score}, Risk={risk_level.value}, "
                f"Gaps={len(gaps)}, Fixes={len(fixes)}"
            )
            
            return (
                score, 
                risk_level, 
                gaps, 
                fixes, 
                summary, 
                references, 
                executive_summary_dict
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed: {e}")
            if 'response' in locals():
                logger.error(f"Response preview: {response[:1000]}")
            raise AIServiceError(
                f"AI returned invalid JSON: {str(e)}", 
                error_code="INVALID_AI_RESPONSE"
            )
        
        except AIServiceError:
            # Re-raise AIServiceError as-is
            raise
        
        except ValidationError:
            # Re-raise ValidationError as-is
            raise
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {str(e)}", exc_info=True)
            raise AIServiceError(
                f"Policy analysis failed: {str(e)}", 
                error_code="ANALYSIS_FAILED"
            )
    
    def _get_analysis_prompt(
        self, 
        request: PolicyAnalysisRequest,
        policy_text: str
    ) -> str:
        """
        Generate analysis prompt with dynamic sizing based on policy length
        
        Args:
            request: The policy analysis request
            policy_text: The policy text (already truncated if needed)
            
        Returns:
            Formatted prompt string
        """
        # Estimate tokens (rough: 1 token ≈ 4 chars)
        policy_tokens = len(policy_text) // 4
        template_tokens = len(self.analysis_prompt_template) // 4
        total_estimated_tokens = policy_tokens + template_tokens
        
        # Gemini 2.0 Flash has ~1M token context, but let's be conservative
        max_safe_tokens = 100000  # Leave room for response
        
        if total_estimated_tokens > max_safe_tokens:
            # Use abbreviated prompt for very long policies
            logger.warning(
                f"Using abbreviated prompt due to length "
                f"(estimated {total_estimated_tokens} tokens)"
            )
            return self._get_abbreviated_prompt(request, policy_text)
        else:
            # Use full comprehensive prompt
            return self.analysis_prompt_template.format(
                company_name=request.company_name,
                industry=request.industry or 'Unknown',
                document_type=request.document_type.value,
                company_size=getattr(request, 'company_size', 'Unknown'),
                target_users=getattr(request, 'target_users', 'General Public'),
                processing_scope=getattr(request, 'processing_scope', 'Standard'),
                document_text=policy_text
            )

    def _get_abbreviated_prompt(
        self, 
        request: PolicyAnalysisRequest,
        policy_text: str
    ) -> str:
        """
        Abbreviated prompt for long policies
        
        Args:
            request: The policy analysis request
            policy_text: The policy text
            
        Returns:
            Abbreviated prompt string
        """
        return f"""
You are a Nigerian data protection expert with deep NDPA 2023 expertise. 
Analyze this privacy policy for compliance.

COMPANY: {request.company_name}
INDUSTRY: {request.industry or 'Unknown'}
DOCUMENT TYPE: {request.document_type.value}

POLICY TEXT:
{policy_text}

CRITICAL FOCUS AREAS:
1. Data Subject Rights (NDPA S. 34-39) - ALL 8 rights must be addressed
2. Lawful Basis (S. 25-26) - Clear legal basis and consent requirements
3. Security Measures (S. 31-33) - Technical and organizational measures
4. Data Protection Officer (S. 5-6) - Mandatory DPO appointment and contact
5. Breach Notification (S. 40-41) - 72-hour notification procedures
6. Special Category Data (S. 27) - Sensitive data handling
7. Children's Data (S. 28) - Under 18 protection
8. Cross-Border Transfers (S. 43-46) - International data transfer safeguards

SCORING CRITERIA:
- Base: 100 points
- CRITICAL gaps (-25 to -40 each): Missing DPO, no breach procedures, unlawful processing
- HIGH gaps (-15 to -25 each): Missing rights, weak consent, no retention periods
- MEDIUM gaps (-8 to -15 each): Partial coverage, unclear language
- LOW gaps (-2 to -8 each): Minor issues, best practice gaps

RESPOND IN JSON FORMAT:
{{
  "compliance_score": 0-120,
  "risk_level": "low/medium/high/critical",
  "gaps": [
    {{
      "gap_id": "gap_001",
      "title": "Short descriptive title",
      "description": "Detailed explanation of what's missing and why it violates NDPA",
      "severity": "critical/high/medium/low",
      "ndpr_articles": ["S. 25", "S. 26"],
      "impact": "Regulatory, operational, and legal risks",
      "recommendation": "Specific actionable steps to fix"
    }}
  ],
  "executive_summary": {{
    "overall_assessment": "Brief narrative assessment",
    "key_strengths": ["Strength 1", "Strength 2"],
    "critical_weaknesses": ["Weakness 1", "Weakness 2"],
    "immediate_actions": ["Action 1 (0-7 days)", "Action 2 (0-7 days)"],
    "compliance_roadmap": "Phased remediation plan",
    "estimated_total_remediation_cost": "NGN X - Y",
    "estimated_compliance_timeline": "X months"
  }},
  "legal_references": [
    {{
      "regulation": "NDPA 2023",
      "article": "S. 25",
      "title": "Article title",
      "summary": "Plain language explanation",
      "relevance": "Why this matters"
    }}
  ]
}}

Return ONLY valid JSON. Be thorough but concise.
"""
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        ULTRA-ROBUST JSON parser for Gemini AI responses
        Handles ALL common JSON formatting issues with multiple fallback strategies
        """
        logger.info(f"🔄 Parsing AI response ({len(response)} chars)")
        
        # Strategy 0: Try direct parsing first (ideal case)
        try:
            result = json.loads(response)
            logger.info("✅ Strategy 0: Direct parsing succeeded")
            return self._validate_and_fix_analysis_structure(result)
        except json.JSONDecodeError:
            logger.debug("Strategy 0 failed - trying extraction methods")
        
        # Strategy 1: Extract JSON from markdown code blocks
        json_patterns = [
            r'```(?:json)?\s*({.*?})\s*```',  # ```json { ... } ```
            r'```\s*({.*?})\s*```',           # ``` { ... } ```
            r'({.*})',                         # Anything between { and }
            r'JSON:\s*({.*?})(?=\n|$)',       # JSON: { ... }
            r'response:\s*({.*?})(?=\n|$)',   # response: { ... }
        ]
        
        for i, pattern in enumerate(json_patterns):
            try:
                match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                if match:
                    json_str = match.group(1)
                    result = json.loads(json_str)
                    logger.info(f"✅ Strategy {i+1}: Pattern {pattern[:20]}... succeeded")
                    return self._validate_and_fix_analysis_structure(result)
            except (json.JSONDecodeError, AttributeError) as e:
                logger.debug(f"Strategy {i+1} failed: {e}")
                continue
        
        # Strategy 2: Find first { and last } with validation
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            json_str = response[start_idx:end_idx + 1]
            
            # Try with aggressive cleaning
            try:
                cleaned_json = self._clean_json_string(json_str)
                result = json.loads(cleaned_json)
                logger.info("✅ Strategy 6: Aggressive cleaning succeeded")
                return self._validate_and_fix_analysis_structure(result)
            except json.JSONDecodeError:
                logger.debug("Strategy 6 failed")
        
        # Strategy 3: Try line-by-line reconstruction
        try:
            reconstructed = self._reconstruct_json_from_lines(response)
            if reconstructed:
                result = json.loads(reconstructed)
                logger.info("✅ Strategy 7: Line reconstruction succeeded")
                return self._validate_and_fix_analysis_structure(result)
        except (json.JSONDecodeError, Exception) as e:
            logger.debug(f"Strategy 7 failed: {e}")
        
        # FINAL FALLBACK: Create structured analysis from text content
        logger.warning("⚠️ All parsing strategies failed - creating structured fallback")
        return self._create_fallback_analysis_from_text(response)

    def _validate_and_fix_analysis_structure(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and fix the structure of the analysis to ensure all required fields exist
        """
        # Ensure basic structure exists
        if not isinstance(analysis, dict):
            analysis = {}
        
        # Ensure required top-level fields
        analysis.setdefault('compliance_score', 50)
        analysis.setdefault('risk_level', 'high')
        analysis.setdefault('gaps', [])
        analysis.setdefault('executive_summary', {})
        analysis.setdefault('legal_references', [])
        
        # Validate and fix gaps array
        if not isinstance(analysis['gaps'], list):
            analysis['gaps'] = []
        
        # Ensure each gap has required fields
        for i, gap in enumerate(analysis['gaps']):
            if not isinstance(gap, dict):
                analysis['gaps'][i] = {}
            
            gap.setdefault('gap_id', f'gap_{i+1:03d}')
            gap.setdefault('title', 'Unnamed Compliance Gap')
            gap.setdefault('description', 'Description not provided by AI')
            gap.setdefault('severity', 'medium')
            gap.setdefault('ndpr_articles', [])
            gap.setdefault('impact', 'Impact assessment not provided')
            gap.setdefault('recommendation', 'Review policy section manually')
        
        # Ensure executive_summary is a dict with required fields
        if not isinstance(analysis['executive_summary'], dict):
            analysis['executive_summary'] = {}
        
        exec_summary = analysis['executive_summary']
        exec_summary.setdefault('overall_assessment', 'Analysis completed with AI assistance')
        exec_summary.setdefault('key_strengths', [])
        exec_summary.setdefault('critical_weaknesses', [])
        exec_summary.setdefault('immediate_actions', [])
        exec_summary.setdefault('compliance_roadmap', 'Review detailed gaps for remediation plan')
        exec_summary.setdefault('estimated_total_remediation_cost', 'NGN 0 - To be assessed')
        exec_summary.setdefault('estimated_compliance_timeline', 'To be determined based on gaps')
        
        return analysis

    def _reconstruct_json_from_lines(self, response: str) -> Optional[str]:
        """
        Reconstruct JSON by finding JSON-like lines and combining them
        """
        lines = response.split('\n')
        json_lines = []
        in_json = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for JSON start/end markers
            if line.startswith('{') or line.startswith('['):
                in_json = True
            if in_json:
                json_lines.append(line)
            if line.endswith('}') or line.endswith(']'):
                in_json = False
        
        if json_lines:
            reconstructed = ' '.join(json_lines)
            # Validate it's at least somewhat JSON-like
            if reconstructed.count('{') == reconstructed.count('}') and reconstructed.count('{') > 0:
                return reconstructed
        
        return None

    def _create_fallback_analysis_from_text(self, response: str) -> Dict[str, Any]:
        """
        Create a structured analysis by extracting information from the raw text response
        """
        logger.info("🔄 Creating fallback analysis from text content")
        
        # Try to extract score from text
        score_match = re.search(r'score[:\s]*(\d+)', response, re.IGNORECASE)
        score = int(score_match.group(1)) if score_match else 50
        
        # Try to extract gaps information
        gaps = []
        gap_sections = re.findall(r'gap[^}]*', response, re.IGNORECASE | re.DOTALL)
        
        for i, gap_text in enumerate(gap_sections[:5]):  # Limit to 5 gaps
            gap = {
                'gap_id': f'extracted_gap_{i+1:03d}',
                'title': self._extract_field(gap_text, 'title') or 'Compliance Issue Identified',
                'description': self._extract_field(gap_text, 'description') or gap_text[:200] + '...',
                'severity': self._extract_field(gap_text, 'severity') or 'medium',
                'ndpr_articles': self._extract_list_field(gap_text, 'ndpr_articles'),
                'impact': self._extract_field(gap_text, 'impact') or 'Requires manual review',
                'recommendation': self._extract_field(gap_text, 'recommendation') or 'Review policy section'
            }
            gaps.append(gap)
        
        if not gaps:
            # Create at least one meaningful gap based on common issues
            gaps = [{
                'gap_id': 'fallback_gap_001',
                'title': 'Policy Analysis Requires Manual Review',
                'description': 'AI response parsing encountered issues. The policy should be manually reviewed for NDPA compliance.',
                'severity': 'medium',
                'ndpr_articles': ['S. 24', 'S. 25'],
                'impact': 'Automated analysis incomplete',
                'recommendation': 'Have legal counsel review the privacy policy against NDPA 2023 requirements'
            }]
        
        return {
            'compliance_score': score,
            'risk_level': 'high' if score < 70 else 'medium',
            'gaps': gaps,
            'executive_summary': {
                'overall_assessment': 'AI analysis completed with parsing limitations. Manual review recommended for comprehensive assessment.',
                'key_strengths': ['Automated analysis attempted', 'Basic structure identified'],
                'critical_weaknesses': ['AI response parsing issues', 'Requires manual verification'],
                'immediate_actions': ['Review AI response manually', 'Verify compliance gaps with legal expert'],
                'compliance_roadmap': 'Begin with manual policy review, then address identified gaps',
                'estimated_total_remediation_cost': 'NGN 0 - Assessment required',
                'estimated_compliance_timeline': '2-4 weeks with legal support'
            },
            'legal_references': [
                {
                    'regulation': 'NDPA 2023',
                    'article': 'S. 24',
                    'title': 'Data Protection Principles',
                    'summary': 'Personal data must be processed lawfully, fairly, and transparently',
                    'relevance': 'Fundamental compliance requirement'
                }
            ]
        }

    def _extract_field(self, text: str, field: str) -> Optional[str]:
        """Extract a field value from text using patterns"""
        patterns = [
            f'"{field}"[:\s]*"([^"]*)"',
            f"'{field}'[:\s]*'([^']*)'",
            f'{field}[:\s]*([^,\n}}]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_list_field(self, text: str, field: str) -> List[str]:
        """Extract a list field from text"""
        patterns = [
            f'"{field}"[:\s]*\[([^]]*)\]',
            f"'{field}'[:\s]*\[([^]]*)\]", 
            f'{field}[:\s]*\[([^]]*)\]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                items = match.group(1).split(',')
                return [item.strip().strip('"\'') for item in items if item.strip()]
        return []
    
    def _clean_json_string(self, json_str: str) -> str:
        """
        AGGRESSIVE JSON cleaning - fixes common Gemini issues
        """
        
        original = json_str
        
        # 1. Remove ALL comments
                # 1. Remove ALL comments
        json_str = re.sub(r'//.*?$', '',
        json_str, flags=re.MULTILINE)
        json_str = re.sub(r'/\*.*?\*/', '', 
        json_str, flags=re.DOTALL)
        
        # 2. Remove trailing commas
        json_str = re.sub(r',\s*([}$\]])', r'\1', json_str)
        
        # 3. Remove leading commas
        json_str = re.sub(r'([${\[])\s*,', r'\1', json_str)
        
        # 4. Fix missing commas between objects/arrays (CRITICAL!)
        json_str = re.sub(r'}\s*{', '},{', json_str)
        json_str = re.sub(r']\s*\[', '],[', json_str)
        json_str = re.sub(r'}\s*\[', '},[', json_str)
        json_str = re.sub(r']\s*{', '],{', json_str)
        
        # 5. Fix missing commas between key-value pairs
        json_str = re.sub(r'(["\d}\]])[\s\n]*"', r'\1,"', json_str)
        
        # 6. Remove text before { or after }
        start = json_str.find('{')
        end = json_str.rfind('}') + 1
        if start != -1 and end > start:
            json_str = json_str[start:end]
        
        # 7. Fix string escaping issues
        json_str = re.sub(r'(?<!\\)\n', ' ', json_str)
        json_str = re.sub(r'(?<!\\)\r', '', json_str)
        json_str = re.sub(r'\\+"', '"', json_str)
        json_str = re.sub(r'(?<!\\)\t', ' ', json_str)
        
        # 8. Remove multiple consecutive commas
        json_str = re.sub(r',+', ',', json_str)
        
        # 9. Remove commas after colons
        json_str = re.sub(r':\s*,', ':', json_str)
        
        if json_str != original:
            logger.debug(f"JSON cleaned: {len(original)} → {len(json_str)} chars")
        
        return json_str
    
    def _generate_default_summary(self, score: int, gap_count: int) -> str:
        """Generate default summary when AI parsing fails"""
        
        if score >= 85:
            grade = "Good"
        elif score >= 70:
            grade = "Acceptable"
        elif score >= 50:
            grade = "Needs Improvement"
        else:
            grade = "Critical"
        
        return (
            f"Compliance Score: {score}/100 ({grade}). "
            f"Found {gap_count} compliance gap(s). "
            f"Review detailed analysis for remediation steps."
        )
    
    def _extract_compliance_score(self, analysis: Dict) -> int:
        """
        Extract and validate compliance score
        
        Args:
            analysis: Analysis dictionary from AI
            
        Returns:
            Validated compliance score (0-120)
        """
        score = analysis.get('compliance_score', 50)
        
        # Validate score range
        if not isinstance(score, (int, float)):
            logger.warning(f"Invalid score type: {type(score)}, defaulting to 50")
            return 50
        
        score = int(score)
        if score < 0:
            logger.warning(f"Score {score} below 0, capping at 0")
            return 0
        if score > 120:
            logger.warning(f"Score {score} above 120, capping at 120")
            return 120
        
        return score
    
    def _process_gaps(self, gaps_data: List[Dict]) -> List[ComplianceGap]:
        """
        Process gaps from AI response into ComplianceGap objects
        
        Args:
            gaps_data: List of gap dictionaries from AI
            
        Returns:
            List of ComplianceGap objects
        """
        if not gaps_data:
            logger.warning("⚠️ No gaps returned by AI - policy may be excellent or analysis incomplete")
            return []
        
        gaps = []
        for i, gap_dict in enumerate(gaps_data):
            try:
                # Validate required fields
                if not gap_dict.get('title') or not gap_dict.get('description'):
                    logger.warning(f"Skipping gap {i}: missing title or description")
                    continue
                
                # Parse severity
                severity_str = gap_dict.get('severity', 'medium').lower()
                try:
                    severity = RiskLevel(severity_str)
                except ValueError:
                    logger.warning(f"Invalid severity '{severity_str}' for gap {i}, defaulting to MEDIUM")
                    severity = RiskLevel.MEDIUM
                
                # Handle impact field - can be string or dict
                impact = gap_dict.get('impact', 'No impact assessment provided')
                if isinstance(impact, dict):
                    # Format dict impact into readable string
                    impact_parts = []
                    for key, value in impact.items():
                        impact_parts.append(f"{key.title()}: {value}")
                    impact = "\n".join(impact_parts)
                
                gap = ComplianceGap(
                    gap_id=gap_dict.get('gap_id', f"gap_{i:03d}"),
                    title=gap_dict['title'],
                    description=gap_dict['description'],
                    severity=severity,
                    ndpr_articles=gap_dict.get('ndpr_articles', []),
                    impact=impact,
                    recommendation=gap_dict.get('recommendation', 'Address this compliance gap as soon as possible.')
                )
                gaps.append(gap)
                
            except Exception as e:
                logger.warning(f"Failed to process gap {i}: {str(e)}")
                continue
        
        logger.info(f"✅ Processed {len(gaps)} gaps from AI response")
        return gaps
    
    async def _generate_fixes(
        self,
        gaps: List[ComplianceGap],
        original_text: str
    ) -> List[ComplianceFix]:
        """
        Generate detailed fixes for identified compliance gaps
        
        Args:
            gaps: List of compliance gaps
            original_text: Original policy text
            
        Returns:
            List of ComplianceFix objects
        """
        if not gaps:
            return []
        
        logger.info(f"🔧 Generating fixes for {len(gaps)} gaps...")
        fixes = []
        
        # Limit to top 10 most severe gaps to avoid token limits
        priority_gaps = sorted(
            gaps, 
            key=lambda g: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(g.severity.value, 4)
        )[:10]
        
        for gap in priority_gaps:
            try:
                fix = await self._generate_single_fix(gap, original_text)
                if fix:
                    fixes.append(fix)
            except Exception as e:
                logger.warning(f"Failed to generate fix for {gap.gap_id}: {str(e)}")
                # Create fallback fix
                fixes.append(self._create_fallback_fix(gap))
        
        logger.info(f"✅ Generated {len(fixes)} fixes")
        return fixes
    
    async def _generate_single_fix(
        self,
        gap: ComplianceGap,
        original_text: str
    ) -> Optional[ComplianceFix]:
        """
        Generate a single fix for a compliance gap
        
        Args:
            gap: ComplianceGap to fix
            original_text: Original policy text
            
        Returns:
            ComplianceFix object or None if generation fails
        """
        
        prompt = f"""
You are a Nigerian data protection legal expert drafting compliant privacy policy text.

COMPLIANCE GAP:
Title: {gap.title}
Description: {gap.description}
Violated Articles: {', '.join(gap.ndpr_articles)}
Severity: {gap.severity.value}
Recommendation: {gap.recommendation}

TASK: Create a compliant policy clause that fixes this issue according to NDPA 2023 standards.

Your response must:
1. Provide legally compliant text that directly addresses the gap
2. Reference specific NDPA sections where relevant
3. Use clear, accessible language (avoid legal jargon where possible)
4. Include practical implementation steps
5. Be actionable for non-lawyers

FORMAT (Return ONLY valid JSON):
{{
  "suggested_text": "Your compliant clause here with NDPA references...",
  "implementation_steps": [
    "Specific step 1 with responsible party",
    "Specific step 2 with timeline",
    "Specific step 3 with verification method"
  ],
  "effort_level": "low/medium/high",
  "estimated_timeline": "X days/weeks/months",
  "responsible_parties": ["Role 1", "Role 2"],
  "success_criteria": "How to measure successful implementation"
}}

Return ONLY the JSON object, no other text.
"""
        
        try:
            # Use higher temperature for creative fix generation
            response = await self.gemini.generate_text(prompt, temperature=0.4)
            
            # Parse response
            json_text = re.sub(r'```json\s*', '', response)
            json_text = re.sub(r'```\s*', '', json_text)
            json_text = json_text.strip()
            
            fix_data = json.loads(json_text)
            
            return ComplianceFix(
                gap_id=gap.gap_id,
                fix_title=f"Fix: {gap.title}",
                suggested_text=fix_data.get('suggested_text', 'See recommendation for guidance.'),
                implementation_steps=fix_data.get('implementation_steps', ['Review gap details', 'Update policy text', 'Verify compliance']),
                effort_level=fix_data.get('effort_level', 'medium')
            )
            
        except Exception as e:
            logger.warning(f"Fix generation failed for {gap.gap_id}: {e}")
            return None
    
    def _create_fallback_fix(self, gap: ComplianceGap) -> ComplianceFix:
        """
        Create a basic fallback fix when AI generation fails
        
        Args:
            gap: ComplianceGap to create fallback fix for
            
        Returns:
            ComplianceFix object with basic recommendations
        """
        return ComplianceFix(
            gap_id=gap.gap_id,
            fix_title=f"Address: {gap.title}",
            suggested_text=f"Update your privacy policy to address: {gap.description}\n\nRefer to NDPA {', '.join(gap.ndpr_articles)} for specific requirements.",
            implementation_steps=[
                "Review NDPA requirements for this area",
                "Draft compliant policy language",
                "Have legal counsel review changes",
                "Update privacy policy document",
                "Communicate changes to users if required"
            ],
            effort_level="medium"
        )
    
    def _calculate_risk_level(self, score: int) -> RiskLevel:
        """
        Calculate risk level based on compliance score
        
        Args:
            score: Compliance score (0-120)
            
        Returns:
            RiskLevel enum value
        """
        if score >= 85:
            return RiskLevel.LOW
        elif score >= 70:
            return RiskLevel.MEDIUM
        elif score >= 50:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def _get_grade_from_score(self, score: int) -> str:
        """
        Get letter grade from numeric score
        
        Args:
            score: Compliance score (0-120)
            
        Returns:
            Grade string
        """
        if score >= 95:
            return "Platinum"
        elif score >= 85:
            return "Gold"
        elif score >= 70:
            return "Silver"
        elif score >= 50:
            return "Bronze"
        elif score >= 30:
            return "Critical"
        else:
            return "Catastrophic"
    
    def _create_legal_references(
        self,
        gaps: List[ComplianceGap],
        ai_references: List[Dict]
    ) -> List[LegalReference]:
        """
        Create comprehensive legal references from gaps and AI data
        
        Args:
            gaps: List of compliance gaps
            ai_references: Legal references from AI response
            
        Returns:
            List of LegalReference objects
        """
        references = []
        seen_articles = set()
        
        # First, add AI-provided references
        for ref_dict in ai_references:
            try:
                article = ref_dict.get('article', '')
                if article and article not in seen_articles:
                    seen_articles.add(article)
                    references.append(LegalReference(
                        regulation=ref_dict.get('regulation', 'NDPA 2023'),
                        article=article,
                        title=ref_dict.get('title', 'NDPA Provision'),
                        summary=ref_dict.get('summary', ref_dict.get('interpretation', 'See NDPA for details')),
                        relevance=ref_dict.get('relevance', 'Referenced in compliance gaps')
                    ))
            except Exception as e:
                logger.warning(f"Failed to process AI reference: {e}")
                continue
        
        # Then add references from gaps
        for gap in gaps:
            for article in gap.ndpr_articles:
                if article not in seen_articles:
                    seen_articles.add(article)
                    references.append(LegalReference(
                        regulation="NDPA 2023",
                        article=article,
                        title=self._get_article_title(article),
                        summary=self._get_article_summary(article),
                        relevance=f"Violated in: {gap.title}"
                    ))
        
        logger.info(f"✅ Created {len(references)} legal references")
        return references
    
    def _get_article_title(self, article: str) -> str:
        """
        Get human-readable title for NDPA article
        
        Args:
            article: Article reference (e.g., "S. 25")
            
        Returns:
            Human-readable title
        """
        article_titles = {
            # Section 24 - Principles
            "S. 24": "Data Protection Principles",
            "S. 24(1)(a)": "Lawfulness, Fairness and Transparency",
            "S. 24(1)(b)": "Purpose Limitation",
            "S. 24(1)(c)": "Data Minimization",
            "S. 24(1)(d)": "Storage Limitation",
            "S. 24(1)(e)": "Accuracy",
            "S. 24(1)(f)": "Integrity and Confidentiality",
            "S. 24(1)(g)": "Accountability",
            
            # Section 25-26 - Lawful Basis
            "S. 25": "Lawful Basis for Processing",
            "S. 25(1)(a)": "Lawful Basis - Consent",
            "S. 25(1)(b)": "Lawful Basis - Contract",
            "S. 25(1)(c)": "Lawful Basis - Legal Obligation",
            "S. 25(1)(d)": "Lawful Basis - Vital Interest",
            "S. 25(1)(e)": "Lawful Basis - Public Interest",
            "S. 25(1)(f)": "Lawful Basis - Legitimate Interest",
            "S. 26": "Consent Requirements",
            "S. 26(9)": "Children's Consent",
            
            # Section 27-28 - Special Data
            "S. 27": "Special Category Data",
            "S. 28": "Children's Data Protection",
            
            # Section 31-33 - Security
            "S. 31": "Security of Processing",
            "S. 32": "Security Measures",
            "S. 33": "Data Protection Impact Assessment (DPIA)",
            
            # Section 34-39 - Data Subject Rights
            "S. 34": "Right to Information",
            "S. 35": "Right of Access",
            "S. 35(3)": "Right to Data Portability",
            "S. 36": "Right to Rectification",
            "S. 37": "Right to Erasure (Right to be Forgotten)",
            "S. 38": "Right to Restriction of Processing",
            "S. 39": "Right to Object",
            "S. 39(4)": "Right Not to be Subject to Automated Decision-Making",
            
            # Section 40-41 - Breach
            "S. 40": "Data Breach Notification to NDPC",
            "S. 41": "Data Breach Notification to Data Subjects",
            
            # Section 43-46 - Transfers
            "S. 43": "Cross-Border Data Transfers",
            "S. 44": "Transfer Safeguards",
            "S. 45": "Standard Data Protection Clauses",
            "S. 46": "Binding Corporate Rules",
            
            # Section 47 - Records
            "S. 47": "Records of Processing Activities (ROPA)",
            
            # Section 5-6 - DPO
            "S. 5": "Data Protection Officer (DPO)",
            "S. 6": "DPO Duties and Responsibilities",
            
            # Section 65-71 - Penalties
            "S. 65": "Administrative Penalties",
            "S. 71": "Civil Liability and Compensation",
            
            # Old NDPR format (backward compatibility)
            "2.1": "Lawfulness and Consent (NDPR)",
            "2.2": "Purpose Limitation (NDPR)",
            "2.3": "Data Minimization (NDPR)",
            "2.4": "Storage Limitation (NDPR)",
            "2.5": "Rights of Data Subjects (NDPR)",
            "3.1": "Security of Processing (NDPR)",
            "4.1": "Data Breach Notification (NDPR)"
        }
        
        return article_titles.get(article, f"NDPA Article {article}")
    
    def _get_article_summary(self, article: str) -> str:
        """
        Get plain-language summary for NDPA article
        
        Args:
            article: Article reference (e.g., "S. 25")
            
        Returns:
            Plain-language summary
        """
        article_summaries = {
            "S. 24(1)(a)": "Personal data must be processed lawfully, fairly, and transparently. You must tell people clearly what you're doing with their data.",
            "S. 24(1)(b)": "Only use data for the specific purpose you collected it for. Don't repurpose data without consent.",
            "S. 24(1)(c)": "Only collect data you actually need. Don't ask for unnecessary information.",
            "S. 24(1)(d)": "Don't keep data longer than necessary. Delete or anonymize when done.",
            "S. 24(1)(e)": "Keep data accurate and up-to-date. Let people correct wrong information.",
            "S. 24(1)(f)": "Protect data with appropriate security measures. Prevent breaches and unauthorized access.",
            "S. 24(1)(g)": "You must prove compliance. Keep records and documentation.",
            
            "S. 25(1)(a)": "Get clear consent before processing personal data. Consent must be freely given, specific, informed, and unambiguous.",
            "S. 26": "Consent must be easy to give and withdraw. No pre-checked boxes. Burden of proof is on you.",
            "S. 26(9)": "For children under 18, you need parental/guardian consent. Verify age appropriately.",
            
            "S. 27": "Sensitive data (health, biometrics, religion, etc.) requires explicit consent or specific legal basis.",
            "S. 28": "Children's data requires special protection. Best interests of child must be paramount.",
            
            "S. 31": "Implement appropriate technical and organizational security measures.",
            "S. 33": "Conduct Data Protection Impact Assessment (DPIA) for high-risk processing activities.",
            
            "S. 34": "Provide clear information about data processing at point of collection. Transparency is mandatory.",
            "S. 35": "People can request a copy of their data. Respond within 30 days, free of charge (first request).",
            "S. 35(3)": "Provide data in machine-readable format. Enable direct transfer to another controller.",
            "S. 36": "Let people correct inaccurate or incomplete data. Notify recipients of corrections.",
            "S. 37": "Delete data when requested if: consent withdrawn, no longer needed, unlawful processing, or legal obligation.",
            "S. 38": "Restrict processing when accuracy is contested or during legitimate grounds verification.",
            "S. 39": "People can object to processing, especially for direct marketing. Objection must be honored.",
            "S. 39(4)": "Don't make solely automated decisions with legal/significant effects without human intervention.",
            
            "S. 40": "Notify NDPC within 72 hours of becoming aware of a data breach (if risk exists).",
            "S. 41": "Notify affected individuals without undue delay if breach poses high risk.",
            
            "S. 43": "Don't transfer data outside Nigeria unless adequate protection is ensured.",
            "S. 47": "Maintain written records of all processing activities. Make available to NDPC on request.",
            
            "S. 5": "Appoint a Data Protection Officer (DPO). Mandatory for all controllers and processors.",
            "S. 6": "DPO monitors compliance, advises on obligations, and serves as contact point for NDPC.",
            
            "S. 65": "Fines up to 2% of annual turnover or NGN 10M (whichever higher) for violations; 4% or NGN 25M for serious violations.",
            "S. 71": "Data subjects can sue for compensation for damages from NDPA violations.",
            
            # Old NDPR
            "2.1": "You must get clear permission before collecting personal data.",
            "2.2": "Only use data for the reason you collected it.",
            "2.3": "Only collect data you actually need.",
            "2.4": "Delete data when you no longer need it.",
            "2.5": "People can access, correct, or delete their data.",
            "3.1": "Keep data secure with proper protections.",
            "4.1": "Report data breaches within 72 hours."
        }
        
        return article_summaries.get(article, "See Nigeria Data Protection Act 2023 for full details.")


# Singleton instance management
_legal_analyzer: Optional[LegalAnalyzer] = None


def get_legal_analyzer() -> LegalAnalyzer:
    """
    Get or create singleton LegalAnalyzer instance
    
    Returns:
        LegalAnalyzer instance
    """
    global _legal_analyzer
    if _legal_analyzer is None:
        _legal_analyzer = LegalAnalyzer()
        logger.info("✅ Legal Analyzer initialized")
    return _legal_analyzer


# Utility function for external callers
async def analyze_privacy_policy(request: PolicyAnalysisRequest) -> Dict:
    """
    Convenience function for analyzing a privacy policy
    
    Args:
        request: PolicyAnalysisRequest object with policy details
    
    Returns:
        Dict with analysis results
    """
    analyzer = get_legal_analyzer()
    score, risk, gaps, fixes, summary, refs, exec_summary = await analyzer.analyze_policy(request)
    
    return {
        "compliance_score": score,
        "risk_level": risk.value,
        "total_gaps": len(gaps),
        "gaps": [gap.dict() for gap in gaps],
        "fixes": [fix.dict() for fix in fixes],
        "summary": summary,
        "executive_summary": exec_summary,
        "legal_references": [ref.dict() for ref in refs]
    }


__all__ = ["LegalAnalyzer", "get_legal_analyzer", "analyze_privacy_policy"]
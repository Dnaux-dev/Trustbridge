"""
API Routes for TrustBridge AI-Legal Engine
Enhanced with comprehensive error handling, validation, and monitoring
"""
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import JSONResponse
import logging
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import json
import re

from app.models.schemas import (
    PolicyAnalysisRequest, PolicyAnalysisResponse,
    CitizenActionRequest, CitizenActionResponse,
    QuickComplianceRequest, QuickComplianceResponse,
    HealthCheck, RiskLevel
)
from app.services.legal_analyzer import get_legal_analyzer
from app.services.gemini_service_v2 import get_gemini_service
from app.core.config import settings
from app.core.exceptions import AIServiceError, ServiceError, ValidationError, RateLimitError

logger = logging.getLogger(__name__)

# Create router with enhanced configuration
router = APIRouter(
    prefix="/api/v1",
    tags=["AI Legal Engine"],
    responses={
        500: {"description": "Internal server error"},
        429: {"description": "Rate limit exceeded"},
        400: {"description": "Invalid request"}
    }
)


# ═══════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def parse_json_response(response_text: str) -> Dict[str, Any]:
    """
    Robust JSON parsing from AI responses
    Handles markdown code blocks and malformed JSON
    
    Args:
        response_text: Raw response text
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        ValueError: If JSON parsing fails
    """
    try:
        # Remove markdown code blocks
        json_text = response_text.strip()
        json_text = re.sub(r'```json\s*', '', json_text)
        json_text = re.sub(r'```\s*', '', json_text)
        json_text = json_text.strip()
        
        # Try to extract JSON object if embedded in text
        json_match = re.search(r'\{.*\}', json_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
        
        return json.loads(json_text)
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        logger.error(f"Problematic text (first 500 chars): {response_text[:500]}")
        raise ValueError(f"Invalid JSON response from AI: {e}")


def log_request_metrics(
    endpoint: str,
    duration_ms: int,
    success: bool,
    error: Optional[str] = None
):
    """
    Log request metrics for monitoring
    
    Args:
        endpoint: Endpoint name
        duration_ms: Request duration in milliseconds
        success: Whether request was successful
        error: Error message if failed
    """
    status_emoji = "✅" if success else "❌"
    logger.info(
        f"{status_emoji} {endpoint} | {duration_ms}ms | "
        f"{'Success' if success else f'Error: {error}'}"
    )


async def validate_request_size(request_text: str, max_size: int = 50000) -> None:
    """
    Validate request text size to prevent abuse
    
    Args:
        request_text: Text to validate
        max_size: Maximum allowed size in characters
        
    Raises:
        HTTPException: If text exceeds max size
    """
    if len(request_text) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Document exceeds maximum size of {max_size} characters"
        )


def _format_executive_summary(exec_dict: Dict[str, Any]) -> str:
    """
    Format executive summary dict into readable string
    
    Args:
        exec_dict: Executive summary dictionary from AI or string
        
    Returns:
        Formatted executive summary string
    """
    if isinstance(exec_dict, str):
        return exec_dict
    
    if not isinstance(exec_dict, dict):
        return "Executive summary not available."
    
    parts = []
    
    if exec_dict.get('overall_assessment'):
        parts.append(f"📊 OVERALL ASSESSMENT:\n{exec_dict['overall_assessment']}\n")
    
    if exec_dict.get('key_strengths'):
        parts.append("✅ KEY STRENGTHS:")
        for strength in exec_dict['key_strengths']:
            parts.append(f"  • {strength}")
        parts.append("")
    
    if exec_dict.get('critical_weaknesses'):
        parts.append("⚠️ CRITICAL WEAKNESSES:")
        for weakness in exec_dict['critical_weaknesses']:
            parts.append(f"  • {weakness}")
        parts.append("")
    
    if exec_dict.get('immediate_actions'):
        parts.append("🚨 IMMEDIATE ACTIONS REQUIRED:")
        for i, action in enumerate(exec_dict['immediate_actions'], 1):
            parts.append(f"  {i}. {action}")
        parts.append("")
    
    if exec_dict.get('compliance_roadmap'):
        parts.append(f"🗺️ COMPLIANCE ROADMAP:\n{exec_dict['compliance_roadmap']}\n")
    
    if exec_dict.get('estimated_total_remediation_cost'):
        parts.append(f"💰 ESTIMATED COST: {exec_dict['estimated_total_remediation_cost']}")
    
    if exec_dict.get('estimated_compliance_timeline'):
        parts.append(f"⏱️ TIMELINE: {exec_dict['estimated_compliance_timeline']}")
    
    return "\n".join(parts) if parts else "Executive summary not available. See detailed gaps and fixes for compliance guidance."


# ═══════════════════════════════════════════════════════════════
# HEALTH & STATUS ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Comprehensive health check for all AI services
    
    Returns:
        - System status
        - Gemini AI connectivity
        - Version information
        - Service availability
    """
    try:
        gemini = get_gemini_service()
        
        # Test Gemini connection with timeout
        try:
            gemini_ok = await gemini.test_connection()
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            gemini_ok = False
        
        # Test legal analyzer initialization
        try:
            analyzer = get_legal_analyzer()
            analyzer_ok = analyzer is not None
        except Exception as e:
            logger.error(f"Legal analyzer health check failed: {e}")
            analyzer_ok = False
        
        # Determine overall status
        if gemini_ok and analyzer_ok:
            overall_status = "healthy"
        elif gemini_ok or analyzer_ok:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return HealthCheck(
            status=overall_status,
            version=settings.APP_VERSION,
            gemini_status="connected" if gemini_ok else "error",
            vector_db_status="not_configured",
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return HealthCheck(
            status="unhealthy",
            version=settings.APP_VERSION,
            gemini_status="error",
            vector_db_status="error",
            error_message=str(e),
            timestamp=datetime.utcnow().isoformat()
        )


@router.get("/status")
async def service_status():
    """
    Detailed service status for monitoring
    
    Returns extended health information including:
    - Service uptime
    - Request statistics
    - Resource availability
    """
    return {
        "service": "TrustBridge AI-Legal Engine",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/api/v1/health",
            "analyze_policy": "/api/v1/analyze/policy",
            "validate_action": "/api/v1/validate/action",
            "quick_check": "/api/v1/check/compliance"
        }
    }


# ═══════════════════════════════════════════════════════════════
# POLICY ANALYSIS ENDPOINT (CORE INNOVATION)
# ═══════════════════════════════════════════════════════════════

@router.post("/analyze/policy", response_model=PolicyAnalysisResponse)
async def analyze_policy(
    request: PolicyAnalysisRequest,
    background_tasks: BackgroundTasks,
    http_request: Request
):
    """
    🎯 CORE INNOVATION: AI-Powered NDPR/NDPA Compliance Analysis
    
    Performs exhaustive forensic analysis of privacy policies against:
    - Nigeria Data Protection Act (NDPA) 2023
    - Constitutional privacy rights
    - Sector-specific regulations
    - International best practices (GDPR alignment)
    
    Returns:
    - Compliance score (0-120) with letter grade
    - Detailed gap analysis with severity ratings
    - Actionable fixes with implementation steps
    - Legal references and citations
    - Executive summary with roadmap
    
    Processing:
    - Analyzes up to 15,000 characters of policy text
    - Tests against 67 use case scenarios
    - Validates all 8 data subject rights
    - Checks 7 foundational principles
    - Assesses sector-specific compliance
    """
    start_time = time.time()
    analysis_id = str(uuid.uuid4())
    
    logger.info(
        f"📋 Policy Analysis Request [{analysis_id}] | "
        f"Company: {request.company_name} | "
        f"Industry: {request.industry or 'Unknown'} | "
        f"Document: {len(request.document_text)} chars"
    )
    
    try:
        # Validate request
        await validate_request_size(request.document_text, max_size=50000)
        
        if not request.document_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document text cannot be empty"
            )
        
        # Get analyzer instance
        analyzer = get_legal_analyzer()
        
        # Perform analysis - unpack 7 values
        (
            score, 
            risk_level, 
            gaps, 
            fixes, 
            summary, 
            references, 
            executive_summary_dict
        ) = await analyzer.analyze_policy(request)
        
        # Format executive summary for response
        executive_summary = _format_executive_summary(executive_summary_dict)
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)
        
        # Extract unique NDPR articles
        unique_articles = set()
        for gap in gaps:
            unique_articles.update(gap.ndpr_articles)
        
        # Create detailed analysis summary
        detailed_analysis = (
            f"Comprehensive NDPR/NDPA compliance analysis completed. "
            f"Identified {len(gaps)} compliance gaps across {len(unique_articles)} legal provisions. "
            f"Analysis covered: foundational principles, data subject rights, controller obligations, "
            f"special category data, children's data protection, and cross-border transfers. "
            f"Grade: {_get_grade_from_score(score)}. "
            f"Risk Level: {risk_level.value.upper()}."
        )
        
        # Build response
        response = PolicyAnalysisResponse(
            analysis_id=analysis_id,
            company_name=request.company_name,
            compliance_score=score,
            risk_level=risk_level,
            gaps=gaps,
            fixes=fixes,
            executive_summary=executive_summary,
            detailed_analysis=detailed_analysis,
            legal_context=(
                "Analysis based on Nigeria Data Protection Act (NDPA) 2023, "
                "Nigeria Data Protection Regulation (NDPR) 2019, "
                "Constitution of the Federal Republic of Nigeria (S. 37 - Right to Privacy), "
                "and international best practices including GDPR alignment."
            ),
            legal_references=references,
            processing_time_ms=processing_time,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Log success metrics
        log_request_metrics(
            endpoint="analyze_policy",
            duration_ms=processing_time,
            success=True
        )
        
        logger.info(
            f"✅ Analysis Complete [{analysis_id}] | "
            f"Score: {score}/100 | "
            f"Grade: {_get_grade_from_score(score)} | "
            f"Risk: {risk_level.value} | "
            f"Gaps: {len(gaps)} | "
            f"Time: {processing_time}ms"
        )
        
        # Schedule background cleanup/logging
        background_tasks.add_task(
            _log_analysis_completion,
            analysis_id,
            score,
            len(gaps),
            processing_time
        )
        
        return response
    
    except ValidationError as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_request_metrics(
            endpoint="analyze_policy",
            duration_ms=processing_time,
            success=False,
            error=f"Validation: {str(e)}"
        )
        logger.error(f"❌ Validation Error [{analysis_id}]: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": e.error_code,
                "message": e.message,
                "analysis_id": analysis_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    except AIServiceError as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_request_metrics(
            endpoint="analyze_policy",
            duration_ms=processing_time,
            success=False,
            error=f"AI Service: {str(e)}"
        )
        logger.error(f"❌ AI Service Error [{analysis_id}]: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": e.error_code,
                "message": e.message,
                "analysis_id": analysis_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        
        log_request_metrics(
            endpoint="analyze_policy",
            duration_ms=processing_time,
            success=False,
            error=str(e)
        )
        
        logger.error(
            f"❌ Analysis Failed [{analysis_id}] | "
            f"Error: {str(e)} | "
            f"Time: {processing_time}ms",
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Analysis failed",
                "message": str(e),
                "analysis_id": analysis_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# ═══════════════════════════════════════════════════════════════
# CITIZEN ACTION VALIDATION ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.post("/validate/action", response_model=CitizenActionResponse)
async def validate_citizen_action(
    request: CitizenActionRequest,
    background_tasks: BackgroundTasks
):
    """
    ⚖️ Validate Citizen Data Rights Actions
    
    Determines if a citizen's action is legally valid under NDPR/NDPA and
    generates proof certificate for enforcement.
    
    Supported Actions:
    - REVOKE_CONSENT: Withdraw data processing consent
    - REQUEST_DELETION: Right to erasure/be forgotten
    - REQUEST_ACCESS: Subject access request (SAR)
    - REQUEST_RECTIFICATION: Correct inaccurate data
    - REQUEST_PORTABILITY: Data portability
    - OBJECT_PROCESSING: Object to processing
    - RESTRICT_PROCESSING: Request processing restriction
    
    Returns:
    - Legal validity determination
    - NDPR/NDPA legal basis (specific sections)
    - Plain-language explanation for citizens
    - Legal explanation for enforcement
    - Next steps and timeline
    - Company obligations
    - Proof certificate for records
    """
    start_time = time.time()
    action_id = str(uuid.uuid4())
    
    logger.info(
        f"⚖️ Action Validation Request [{action_id}] | "
        f"Action: {request.action_type.value} | "
        f"Company: {request.company_name} | "
        f"Citizen: {request.citizen_id}"
    )
    
    try:
        gemini = get_gemini_service()
        
        # Create comprehensive validation prompt
        prompt = f"""
You are a senior Nigerian data protection lawyer specializing in NDPR/NDPA citizen rights enforcement.

CITIZEN ACTION REQUEST:
- Action Type: {request.action_type.value}
- Target Company: {request.company_name}
- Data Types Involved: {', '.join(request.data_types)}
- Citizen's Reason: {request.reason or 'Not provided'}
- Citizen ID: {request.citizen_id}

LEGAL FRAMEWORK:
The Nigeria Data Protection Act (NDPA) 2023 provides the following data subject rights:

1. Right to Information (S. 34)
2. Right of Access (S. 35) - Response within 30 days
3. Right to Rectification (S. 36)
4. Right to Erasure/Right to be Forgotten (S. 37)
5. Right to Restriction of Processing (S. 38)
6. Right to Data Portability (S. 35(3))
7. Right to Object (S. 39) - Absolute for marketing
8. Right Not to be Subject to Automated Decision-Making (S. 39(4))

Consent Requirements (S. 26):
- Must be freely given, specific, informed, unambiguous
- Easy withdrawal (as easy as giving consent)
- Controller bears burden of proof

TASK: Determine if this citizen action is legally valid under NDPA 2023.

ANALYSIS REQUIREMENTS:
1. Map action to specific NDPA section(s)
2. Determine legal validity
3. Identify company's legal obligations
4. Specify timeline for compliance
5. Provide plain-language explanation for citizen
6. Provide legal explanation for enforcement/court

RESPOND IN JSON FORMAT:
{{
  "is_legal": true/false,
  "legal_basis": "NDPA Section X.X - [Title]",
  "supporting_articles": ["S. 34", "S. 35", "etc"],
  "plain_explanation": "In simple terms: You have the right to [action] because... The company must respond within [X] days.",
  "legal_explanation": "Under NDPA Section X, the data subject has an absolute/conditional right to [action]. The controller must...",
  "validity_conditions": ["Condition 1 that must be met", "Condition 2"],
  "exceptions": ["Exception 1 where right may not apply", "Exception 2"],
  "next_steps": [
    "1. Submit formal request to company's Data Protection Officer",
    "2. Company has X days to respond",
    "3. If no response, file complaint with NDPC"
  ],
  "company_obligations": [
    "Must acknowledge request within 3 days",
    "Must complete action within 30 days",
    "Must provide written confirmation",
    "Must notify third parties if data was disclosed"
  ],
  "timeline": "Company must respond within 30 days of request (NDPA S. 35). Failure to comply may result in NDPC enforcement action.",
  "enforcement_options": [
    "File complaint with Nigeria Data Protection Commission (NDPC)",
    "Seek civil remedy under NDPA S. 71",
    "Escalate to Federal High Court"
  ],
  "potential_penalties_for_company": "Non-compliance may result in fines up to 2% of annual turnover or NGN 10,000,000 (whichever is higher) under NDPA S. 65.",
  "additional_rights": ["Other related rights citizen should know about"]
}}

Return ONLY valid JSON, no other text.
"""
        
        # Get AI validation
        response_text = await gemini.generate_text(prompt, temperature=0.2)
        result = parse_json_response(response_text)
        
        # Validate required fields
        required_fields = ['is_legal', 'legal_basis', 'plain_explanation', 
                          'legal_explanation', 'next_steps', 'company_obligations', 'timeline']
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field in AI response: {field}")
        
        # Generate comprehensive proof certificate
        proof_text = _generate_proof_certificate(
            action_id=action_id,
            request=request,
            result=result
        )
        
        # Create legal references from supporting articles
        legal_references = []
        for article in result.get('supporting_articles', [result['legal_basis']]):
            legal_references.append({
                "regulation": "NDPA 2023",
                "article": article,
                "title": _get_article_title(article),
                "summary": _get_article_summary(article)
            })
        
        processing_time = int((time.time() - start_time) * 1000)
        
        response = CitizenActionResponse(
            action_id=action_id,
            is_legal=result['is_legal'],
            legal_basis=result['legal_basis'],
            plain_explanation=result['plain_explanation'],
            legal_explanation=result['legal_explanation'],
            next_steps=result['next_steps'],
            company_obligations=result['company_obligations'],
            timeline=result['timeline'],
            proof_text=proof_text,
            legal_references=legal_references,
            timestamp=datetime.utcnow().isoformat()
        )
        
        log_request_metrics(
            endpoint="validate_action",
            duration_ms=processing_time,
            success=True
        )
        
        logger.info(
            f"✅ Action Validated [{action_id}] | "
            f"Valid: {result['is_legal']} | "
            f"Basis: {result['legal_basis']} | "
            f"Time: {processing_time}ms"
        )
        
        return response
    
    except ValueError as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_request_metrics(
            endpoint="validate_action",
            duration_ms=processing_time,
            success=False,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid AI response: {str(e)}"
        )
    
    except AIServiceError as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_request_metrics(
            endpoint="validate_action",
            duration_ms=processing_time,
            success=False,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": e.error_code,
                "message": e.message,
                "action_id": action_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_request_metrics(
            endpoint="validate_action",
            duration_ms=processing_time,
            success=False,
            error=str(e)
        )
        
        logger.error(
            f"❌ Action Validation Failed [{action_id}] | Error: {str(e)}",
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Validation failed",
                "message": str(e),
                "action_id": action_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# ═══════════════════════════════════════════════════════════════
# QUICK COMPLIANCE CHECK ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.post("/check/compliance", response_model=QuickComplianceResponse)
async def quick_compliance_check(
    request: QuickComplianceRequest,
    background_tasks: BackgroundTasks
):
    """
    🔍 Quick NDPR Compliance Check
    
    Fast compliance assessment for specific business practices without
    full policy analysis. Ideal for:
    - Testing new features before launch
    - Validating data collection practices
    - Quick risk assessment
    - Pre-implementation compliance checks
    
    Analyzes:
    - NDPR/NDPA compliance status
    - Risk level assessment
    - Specific compliance issues
    - Quick-win recommendations
    - Sector-specific considerations
    
    Response Time: <5 seconds (vs. 30-60s for full analysis)
    """
    start_time = time.time()
    check_id = str(uuid.uuid4())
    
    logger.info(
        f"🔍 Quick Compliance Check [{check_id}] | "
        f"Practice: {request.practice_description[:80]}... | "
        f"Industry: {request.industry or 'Unknown'}"
    )
    
    try:
        await validate_request_size(request.practice_description, max_size=5000)
        
        if not request.practice_description.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Practice description cannot be empty"
            )
        
        gemini = get_gemini_service()
        
        # Create focused compliance check prompt
        prompt = f"""
You are an NDPR/NDPA compliance expert performing a rapid risk assessment.

BUSINESS PRACTICE:
{request.practice_description}

CONTEXT:
- Company Size: {request.company_size or 'Unknown'}
- Industry: {request.industry or 'Unknown'}
- Target Users: {getattr(request, 'target_users', 'General Public')}

NDPR/NDPA QUICK CHECK CRITERIA:
1. Lawful Basis: Is there a clear legal basis for data processing?
2. Consent: If consent-based, is it freely given, specific, informed?
3. Purpose Limitation: Is purpose clear and legitimate?
4. Data Minimization: Is only necessary data collected?
5. Transparency: Are users informed clearly?
6. Security: Are appropriate security measures in place?
7. Data Subject Rights: Can users exercise their rights?
8. Special Category Data: Any sensitive data (health, biometrics, etc)?
9. Children's Data: Processing data of minors (under 18)?
10. Cross-Border: Any international data transfers?

TASK: Rapid compliance assessment - identify red flags and quick fixes.

RESPOND IN JSON FORMAT:
{{
  "is_compliant": true/false,
  "score": 0-100,
  "risk_level": "low/medium/high/critical",
  "risk_factors": [
    "Specific risk factor 1 with severity",
    "Specific risk factor 2 with severity"
  ],
  "issues": [
    "Issue 1: Missing consent mechanism for marketing emails",
    "Issue 2: No data retention period specified"
  ],
  "recommendations": [
    "Implement double opt-in for email marketing (NDPA S. 26)",
    "Define retention period (NDPA S. 24(1)(d))"
  ],
  "quick_fixes": [
    "Add 'I agree to marketing emails' checkbox (unchecked by default) - 1 day",
    "Add 'We retain data for 2 years' to policy - 2 hours"
  ],
  "legal_concerns": [
    "NDPA Section X.X: Specific legal concern",
    "NDPA Section Y.Y: Another concern"
  ],
  "estimated_fix_effort": "X hours/days/weeks",
  "estimated_fix_cost": "NGN X - Y or Low/Medium/High"
}}

Return ONLY valid JSON, no other text.
"""
        
        response_text = await gemini.generate_text(prompt, temperature=0.3)
        result = parse_json_response(response_text)
        
        # Validate and extract data
        is_compliant = result.get('is_compliant', False)
        score = min(100, max(0, int(result.get('score', 50))))
        risk_level_str = result.get('risk_level', 'medium').lower()
        
        try:
            risk_level = RiskLevel(risk_level_str)
        except ValueError:
            logger.warning(f"Invalid risk level '{risk_level_str}', defaulting to MEDIUM")
            risk_level = RiskLevel.MEDIUM
        
        # Create legal references from concerns
        legal_references = []
        for concern in result.get('legal_concerns', []):
            # Extract article reference if present
            article_match = re.search(r'S\.\s*\d+(?:\(\d+\))?(?:\([a-z]\))?', concern)
            if article_match:
                article = article_match.group(0)
                legal_references.append({
                    "regulation": "NDPA 2023",
                    "article": article,
                    "title": _get_article_title(article),
                    "summary": concern
                })
        
        processing_time = int((time.time() - start_time) * 1000)
        
        response = QuickComplianceResponse(
            check_id=check_id,
            is_compliant=is_compliant,
            score=score,
            risk_level=risk_level,
            issues=result.get('issues', []),
            recommendations=result.get('recommendations', []),
            quick_fixes=result.get('quick_fixes', []),
            legal_references=legal_references,
            processing_time_ms=processing_time,
            timestamp=datetime.utcnow().isoformat()
        )
        
        log_request_metrics(
            endpoint="quick_compliance",
            duration_ms=processing_time,
            success=True
        )
        
        logger.info(
            f"✅ Quick Check Complete [{check_id}] | "
            f"Compliant: {is_compliant} | "
            f"Score: {score} | "
            f"Risk: {risk_level.value} | "
            f"Time: {processing_time}ms"
        )
        
        return response
    
    except HTTPException:
        raise
    
    except AIServiceError as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_request_metrics(
            endpoint="quick_compliance",
            duration_ms=processing_time,
            success=False,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": e.error_code,
                "message": e.message,
                "check_id": check_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_request_metrics(
            endpoint="quick_compliance",
            duration_ms=processing_time,
            success=False,
            error=str(e)
        )
        
        logger.error(
            f"❌ Quick Check Failed [{check_id}] | Error: {str(e)}",
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Compliance check failed",
                "message": str(e),
                "check_id": check_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _get_grade_from_score(score: int) -> str:
    """Convert numeric score to letter grade"""
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


def _generate_proof_certificate(
    action_id: str,
    request: CitizenActionRequest,
    result: Dict[str, Any]
) -> str:
    """Generate comprehensive proof certificate for citizen action"""
    from datetime import datetime
    
    # Extract data safely
    is_legal = "YES" if result.get('is_legal', False) else "NO"
    legal_basis = result.get('legal_basis', 'Not specified')
    plain_explanation = result.get('plain_explanation', 'Not available')
    legal_explanation = result.get('legal_explanation', 'Not available')
    timeline = result.get('timeline', 'Not specified')
    supporting_articles = result.get('supporting_articles', [])
    company_obligations = result.get('company_obligations', [])
    next_steps = result.get('next_steps', [])
    enforcement_options = result.get('enforcement_options', ['File complaint with NDPC'])
    potential_penalties = result.get('potential_penalties_for_company', 'See NDPA Section 65-71')
    
    # Format strings
    data_types_str = ', '.join(request.data_types) if request.data_types else 'Not specified'
    articles_str = ', '.join(supporting_articles) if supporting_articles else 'Not specified'
    
    # Pre-format sections - BUILD STRINGS BEFORE f-string!
    obligations_section = ""
    if company_obligations:
        for i, obligation in enumerate(company_obligations, 1):
            obligations_section += f"  {i}. {obligation}\n"
    else:
        obligations_section = "  No obligations identified\n"
    
    next_steps_section = ""
    if next_steps:
        for step in next_steps:
            next_steps_section += f"  • {step}\n"
    else:
        next_steps_section = "  Contact NDPC\n"
    
    enforcement_section = ""
    if enforcement_options:
        for option in enforcement_options:
            enforcement_section += f"  • {option}\n"
    else:
        enforcement_section = "  • File complaint with NDPC\n"
    
    current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    iso_time = datetime.utcnow().isoformat()
    
    certificate = f"""
═══════════════════════════════════════════════════════════════
NIGERIA DATA PROTECTION ACT (NDPA) 2023
CITIZEN DATA RIGHTS - LEGAL ACTION CERTIFICATE
═══════════════════════════════════════════════════════════════

Certificate ID: {action_id}
Issue Date: {current_time}
Legal Framework: Nigeria Data Protection Act 2023

CITIZEN INFORMATION:
- Citizen ID: {request.citizen_id}
- Action Type: {request.action_type.value}
- Target Company: {request.company_name}
- Data Types Affected: {data_types_str}
- Reason: {request.reason or 'Not provided'}

LEGAL DETERMINATION:
- Legally Valid: {is_legal}
- Legal Basis: {legal_basis}
- Supporting Articles: {articles_str}

PLAIN LANGUAGE EXPLANATION:
{plain_explanation}

LEGAL EXPLANATION:
{legal_explanation}

COMPANY OBLIGATIONS:
{obligations_section}
TIMELINE:
{timeline}

NEXT STEPS:
{next_steps_section}
ENFORCEMENT OPTIONS:
{enforcement_section}
PENALTIES FOR NON-COMPLIANCE:
{potential_penalties}

═══════════════════════════════════════════════════════════════
CERTIFICATE AUTHENTICATION
═══════════════════════════════════════════════════════════════

Generated by TrustBridge AI-Legal Engine
Certificate ID: {action_id}
Timestamp: {iso_time}

NDPC Contact: https://ndpc.gov.ng
NDPC Email: info@ndpc.gov.ng

═══════════════════════════════════════════════════════════════
"""
    
    return certificate


def _get_article_title(article: str) -> str:
    """Get human-readable title for NDPA article"""
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
        "S. 26": "Consent Requirements",

        # Section 27-28 - Special Data
        "S. 27": "Special Category Data",
        "S. 28": "Children's Data Protection",

        # Section 31-33 - Security
        "S. 31": "Security of Processing",
        "S. 32": "Security Measures",
        "S. 33": "Data Protection Impact Assessment",

        # Section 34-39 - Data Subject Rights
        "S. 34": "Right to Information",
        "S. 35": "Right of Access",
        "S. 35(3)": "Right to Data Portability",
        "S. 36": "Right to Rectification",
        "S. 37": "Right to Erasure",
        "S. 38": "Right to Restriction",
        "S. 39": "Right to Object",
        "S. 39(4)": "Right Against Automated Decisions",

        # Section 40-41 - Breach
        "S. 40": "Breach Notification to NDPC",
        "S. 41": "Breach Notification to Data Subjects",

        # Section 43-46 - Transfers
        "S. 43": "Cross-Border Transfers",
        "S. 44": "Transfer Safeguards",
        "S. 45": "Standard Data Protection Clauses",
        "S. 46": "Binding Corporate Rules",

        # Section 47 - Records
        "S. 47": "Records of Processing Activities",

        # Section 5-6 - DPO
        "S. 5": "Data Protection Officer",
        "S. 6": "DPO Duties"
    }

    return article_titles.get(article, f"NDPA {article}")


def _get_article_summary(article: str) -> str:
    """Get plain-language summary for NDPA article"""
    article_summaries = {
        "S. 24(1)(a)": "Process data lawfully, fairly, and transparently",
        "S. 24(1)(b)": "Use data only for stated purposes",
        "S. 24(1)(c)": "Collect only necessary data",
        "S. 24(1)(d)": "Don't keep data longer than needed",
        "S. 24(1)(e)": "Keep data accurate and up-to-date",
        "S. 24(1)(f)": "Protect data with security measures",
        "S. 24(1)(g)": "Prove compliance with documentation",

        "S. 25": "Establish lawful basis for processing",
        "S. 26": "Get proper consent - freely given, specific, informed",

        "S. 27": "Sensitive data requires explicit consent",
        "S. 28": "Protect children's data (under 18)",

        "S. 31": "Implement security measures",
        "S. 33": "Conduct impact assessments for high-risk processing",

        "S. 34": "Provide clear information about processing",
        "S. 35": "Allow access to personal data within 30 days",
        "S. 35(3)": "Provide data in portable format",
        "S. 36": "Allow correction of inaccurate data",
        "S. 37": "Delete data when requested (with exceptions)",
        "S. 38": "Restrict processing when contested",
        "S. 39": "Allow objection to processing",
        "S. 39(4)": "Require human review of automated decisions",

        "S. 40": "Report breaches to NDPC within 72 hours",
        "S. 41": "Notify affected individuals of breaches",

        "S. 43": "Ensure adequate protection for international transfers",
        "S. 47": "Maintain processing records",

        "S. 5": "Appoint qualified Data Protection Officer",
        "S. 6": "DPO monitors compliance and advises"
    }

    return article_summaries.get(article, "See NDPA 2023 for details")


async def _log_analysis_completion(
    analysis_id: str,
    score: int,
    gap_count: int,
    processing_time: int
):
    """
    Background task to log analysis completion metrics

    Args:
        analysis_id: Unique analysis identifier
        score: Compliance score
        gap_count: Number of gaps identified
        processing_time: Processing time in milliseconds
    """
    try:
        logger.info(
            f"📊 Analysis Metrics [{analysis_id}] | "
            f"Score: {score} | "
            f"Gaps: {gap_count} | "
            f"Time: {processing_time}ms"
        )

        # Here you could add:
        # - Database logging
        # - Analytics tracking
        # - Usage metrics
        # - Cost tracking

    except Exception as e:
        logger.error(f"Failed to log analysis metrics: {e}")


# ═══════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════

__all__ = [
    "router",
    "health_check",
    "analyze_policy",
    "validate_citizen_action",
    "quick_compliance_check"
]

"""
Clean, organized data models for TrustBridge
"""
from pydantic import BaseModel, Field, EmailStr, constr, root_validator, validator
from typing import List, Optional, Dict
from enum import Enum
from pydantic import ConfigDict

model_config = ConfigDict(
    from_attributes=True,         # was: orm_mode
    str_strip_whitespace=True     # was: anystr_strip_whitespace
)





# ============= ENUMS =============


class RiskLevel(str, Enum):
    """Risk level classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"



class DocumentType(str, Enum):
    """Types of documents we can analyze"""
    PRIVACY_POLICY = "privacy_policy"
    TERMS_OF_SERVICE = "terms_of_service"
    CONSENT_FORM = "consent_form"
    DATA_AGREEMENT = "data_agreement"



class ActionType(str, Enum):
    """Types of citizen actions"""
    CONSENT_GRANTED = "consent_granted"
    CONSENT_REVOKED = "consent_revoked"
    DATA_ACCESS = "data_access"
    DATA_DELETION = "data_deletion"



# ============= REQUEST MODELS =============


class PolicyAnalysisRequest(BaseModel):
    """Request to analyze a privacy policy"""
    document_text: constr(min_length=100, max_length=100000) = Field(..., description="Policy text to analyze")
    document_type: DocumentType = Field(default=DocumentType.PRIVACY_POLICY)
    company_name: constr(min_length=2, max_length=100) = Field(..., description="Company or organization name")
    industry: Optional[str] = Field(None, description="Industry sector, e.g., fintech, healthcare")
    company_size: Optional[str] = Field(None, description="Company size category, e.g., small/medium/large")
    target_users: Optional[str] = Field(None, description="Description of policy's target users")
    processing_scope: Optional[str] = Field(None, description="Scope of data processing covered")
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {"document_text": "Your privacy policy text here...",
                "document_type": "privacy_policy",
                "company_name": "TechNova Solutions",
                "industry": "Technology",
                "company_size": "medium",
                "target_users": "General Public",
                "processing_scope": "Standard data processing"
            }
        }
    )


class CitizenActionRequest(BaseModel):
    """Validate a citizen action (e.g., revoking consent)"""
    action_type: ActionType = Field(..., description="Type of citizen action")
    citizen_id: constr(min_length=3, max_length=50) = Field(..., description="Pseudonymized citizen ID")
    company_id: constr(min_length=3, max_length=50) = Field(..., description="Company ID")
    company_name: constr(min_length=2, max_length=100) = Field(..., description="Company name")
    data_types: List[str] = Field(..., description="Data types affected, e.g., ['email', 'phone']")
    reason: Optional[str] = Field(None, description="Reason for the action")

    @validator('data_types')
    def check_data_types_not_empty(cls, v):
        if not v or any(not isinstance(s, str) or not s.strip() for s in v):
            raise ValueError("data_types must be a non-empty list of non-empty strings")
        return v

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {"document_text": "Your privacy policy text here...",
                "document_type": "privacy_policy",
                "company_name": "TechNova Solutions",
                "industry": "Technology",
                "company_size": "medium",
                "target_users": "General Public",
                "processing_scope": "Standard data processing"
            }
        }
    )



class QuickComplianceRequest(BaseModel):
    """Quick compliance check for a practice"""
    practice_description: constr(min_length=20, max_length=2000) = Field(..., description="Description of business practice")
    company_size: Optional[str] = Field(None, description="small/medium/large")
    industry: Optional[str] = None

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {"document_text": "Your privacy policy text here...",
                "document_type": "privacy_policy",
                "company_name": "TechNova Solutions",
                "industry": "Technology",
                "company_size": "medium",
                "target_users": "General Public",
                "processing_scope": "Standard data processing"
            }
        }
    )




# ============= RESPONSE MODELS =============


class LegalReference(BaseModel):
    """Reference to NDPR/GDPR article"""
    regulation: str = Field(..., description="NDPR or GDPR")
    article: str = Field(..., description="e.g., Article 2.2")
    title: str = Field(..., description="Title of the article")
    summary: str = Field(..., description="Plain language summary of the article")
    relevance: str = Field(..., description="Why this applies or is relevant")




class ComplianceGap(BaseModel):
    """A detected compliance violation"""
    gap_id: str = Field(..., description="Unique gap identifier")
    title: str = Field(..., description="Short title/summary of issue")
    description: str = Field(..., description="Detailed description")
    severity: RiskLevel = Field(..., description="Severity level of gap")
    ndpr_articles: List[str] = Field(..., description="List of violated NDPR articles")
    impact: str = Field(..., description="Business impact of the gap")
    recommendation: str = Field(..., description="Recommended remediation action")




class ComplianceFix(BaseModel):
    """AI-generated fix for a gap"""
    gap_id: str = Field(..., description="ID of the gap this fix addresses")
    fix_title: str = Field(..., description="Summary title of fix")
    current_text: Optional[str] = Field(None, description="Current policy text relevant to fix")
    suggested_text: str = Field(..., description="Suggested compliant policy text")
    implementation_steps: List[str] = Field(..., description="Steps to implement fix")
    effort_level: str = Field(..., description="Effort level: low/medium/high")




class PolicyAnalysisResponse(BaseModel):
    """Complete policy analysis result"""
    analysis_id: str = Field(..., description="Unique analysis request id")
    company_name: str = Field(..., description="Company analyzed")
    compliance_score: int = Field(..., ge=0, le=100, description="Overall compliance score (0-100)")
    risk_level: RiskLevel = Field(..., description="Overall risk level")
    
    gaps: List[ComplianceGap] = Field(..., description="List of detected compliance gaps")
    fixes: List[ComplianceFix] = Field(..., description="List of recommended fixes")
    
    executive_summary: str = Field(..., description="High-level overview summary")
    detailed_analysis: str = Field(..., description="Detailed textual analysis")
    legal_context: str = Field(..., description="Context of legal frameworks")
    
    legal_references: List[LegalReference] = Field(..., description="Relevant legal references")
    
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    timestamp: str = Field(..., description="ISO8601 timestamp of analysis")



class CitizenActionResponse(BaseModel):
    """Validation of citizen action"""
    action_id: str = Field(..., description="Unique id for this action validation")
    is_legal: bool = Field(..., description="Is this action legal under NDPR")
    legal_basis: str = Field(..., description="NDPR article supporting this action")
    plain_explanation: str = Field(..., description="Simple explanation")
    legal_explanation: str = Field(..., description="Detailed legal reasoning")
    
    next_steps: List[str] = Field(..., description="Recommended next steps")
    company_obligations: List[str] = Field(..., description="Obligations company must fulfill")
    timeline: str = Field(..., description="Response deadline timeline")
    
    proof_text: str = Field(..., description="Text for legal proof certificate")
    legal_references: List[LegalReference] = Field(..., description="Associated legal references")




class QuickComplianceResponse(BaseModel):
    """Quick compliance check result"""
    is_compliant: bool = Field(..., description="Is the practice compliant?")
    score: int = Field(..., ge=0, le=100, description="Compliance score")
    risk_level: RiskLevel = Field(..., description="Risk level")
    
    issues: List[str] = Field(..., description="List of compliance issue descriptions")
    recommendations: List[str] = Field(..., description="List of suggested fixes")
    quick_fixes: List[str] = Field(..., description="List of quick win fixes")
    
    legal_references: List[LegalReference] = Field(..., description="Legal citations")




class AuditPredictionResponse(BaseModel):
    """Predict NITDA audit outcome"""
    overall_readiness: int = Field(..., ge=0, le=100, description="Overall readiness score")
    predicted_result: str = Field(..., description="Result prediction - PASS/CONDITIONAL/FAIL")
    
    strengths: List[str] = Field(..., description="Identified strengths")
    weaknesses: List[str] = Field(..., description="Identified weaknesses")
    critical_risks: List[Dict[str, str]] = Field(..., description="Critical risks with details")
    
    preparation_plan: List[str] = Field(..., description="Recommended preparation steps")
    estimated_preparation_time: str = Field(..., description="Estimated time for preparation")




# ============= UTILITY MODELS =============


class HealthCheck(BaseModel):
    """API health status"""
    status: str = Field(..., description="Overall system health status")
    version: str = Field(..., description="Application version")
    gemini_status: str = Field(..., description="Connection status to Gemini AI")
    vector_db_status: str = Field(default="not_configured", description="Vector database status")




class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error summary message")
    detail: Optional[str] = Field(None, description="Detailed error info")
    error_code: Optional[str] = Field(None, description="Specific error code")


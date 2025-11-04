import pytest
from app.services.legal_analyzer import LegalAnalyzer
from app.models.schemas import PolicyAnalysisRequest, DocumentType

@pytest.mark.asyncio
async def test_analyze_simple_policy():
    """Test analysis of a simple policy"""
    analyzer = LegalAnalyzer()
    
    request = PolicyAnalysisRequest(
        company_name="Test Company",
        document_type=DocumentType.PRIVACY_POLICY,
        document_text="We collect your email address with your consent. We keep it secure."
    )
    
    score, risk, gaps, fixes, summary, refs, exec_summary = await analyzer.analyze_policy(request)
    
    assert isinstance(score, int)
    assert 0 <= score <= 120
    assert len(gaps) > 0  # Simple policy should have gaps
    assert risk.value in ['low', 'medium', 'high', 'critical']

@pytest.mark.asyncio
async def test_analyze_comprehensive_policy():
    """Test analysis with comprehensive policy"""
    analyzer = LegalAnalyzer()
    
    comprehensive_policy = """
    Privacy Policy
    
    Data Protection Officer: dpo@example.com
    
    We process your data with your consent (NDPA S. 26).
    We collect: name, email, phone for account management.
    Retention: 2 years after account closure.
    Your rights: Access (S. 35), Rectification (S. 36), Erasure (S. 37).
    Security: Encryption and access controls (S. 31).
    Breach notification: Within 72 hours to NDPC (S. 40).
    """
    
    request = PolicyAnalysisRequest(
        company_name="Good Company",
        document_type=DocumentType.PRIVACY_POLICY,
        document_text=comprehensive_policy,
        industry="Technology"
    )
    
    score, risk, gaps, fixes, summary, refs, exec_summary = await analyzer.analyze_policy(request)
    
    assert score > 50  # Should score better than simple policy
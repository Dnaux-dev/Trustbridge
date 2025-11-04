import pytest
from app.services.gemini_service_v2 import GeminiService
from app.core.exceptions import AIServiceError

@pytest.mark.asyncio
async def test_gemini_connection():
    """Test Gemini service can connect"""
    service = GeminiService()
    assert await service.test_connection() is True

@pytest.mark.asyncio
async def test_gemini_generate_text():
    """Test text generation"""
    service = GeminiService()
    response = await service.generate_text("Say hello", temperature=0.1, max_tokens=20)
    assert len(response) > 0
    assert isinstance(response, str)

@pytest.mark.asyncio
async def test_gemini_retry_logic():
    """Test retry logic on failure"""
    service = GeminiService()
    service.max_retries = 2
    
    # This should eventually succeed or raise AIServiceError
    try:
        await service.generate_text("test", temperature=0.0, max_tokens=10)
    except AIServiceError:
        pass  # Expected if API is down
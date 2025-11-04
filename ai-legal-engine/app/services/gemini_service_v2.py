"""
Gemini Service - Fully Async with Proper Error Handling
Enhanced with connection pooling, retries, and safety checks
"""

import google.generativeai as genai
import logging
import asyncio
from typing import Optional
from app.core.config import settings
from app.core.exceptions import AIServiceError

logger = logging.getLogger(__name__)


class GeminiService:
    """Handles all Gemini AI interactions with retries and error handling"""

    def __init__(self):
        """Initialize Gemini service with configuration"""
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
            self.max_retries = 3
            self.base_retry_delay = 1
            logger.info(f"✅ Gemini AI initialized with model '{settings.GEMINI_MODEL}'")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {e}")
            raise AIServiceError(
                f"Gemini initialization failed: {str(e)}",
                error_code="GEMINI_INIT_FAILED"
            )

    async def generate_text(
        self, 
        prompt: str, 
        temperature: float = 0.3, 
        max_tokens: int = 2048
    ) -> str:
        """
        Generate text with retry logic and error handling
        
        Args:
            prompt: The input prompt for generation
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text string
            
        Raises:
            AIServiceError: If generation fails after all retries
        """
        if not prompt or not prompt.strip():
            raise AIServiceError(
                "Prompt cannot be empty",
                error_code="INVALID_PROMPT"
            )
        
        delay = self.base_retry_delay
        last_exception = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Gemini generation attempt {attempt}/{self.max_retries}")
                
                # Use async generate_content method
                response = await self.model.generate_content_async(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    )
                )
                
                # Check if response has candidates
                if not response.candidates or len(response.candidates) == 0:
                    raise AIServiceError(
                        "Gemini returned empty response",
                        error_code="EMPTY_RESPONSE"
                    )
                
                # Check for safety blocks
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = candidate.finish_reason.name if hasattr(
                        candidate.finish_reason, 'name'
                    ) else str(candidate.finish_reason)
                    
                    if finish_reason in ["SAFETY", "BLOCKED_SAFETY"]:
                        logger.warning(f"Response blocked by safety filters: {finish_reason}")
                        raise AIServiceError(
                            f"Content blocked by safety filters: {finish_reason}",
                            error_code="SAFETY_BLOCK"
                        )
                    
                    if finish_reason == "RECITATION":
                        logger.warning("Response blocked due to recitation")
                        raise AIServiceError(
                            "Content blocked due to recitation",
                            error_code="RECITATION_BLOCK"
                        )
                
                # Extract text from response
                if not candidate.content or not candidate.content.parts:
                    raise AIServiceError(
                        "Response has no content parts",
                        error_code="NO_CONTENT"
                    )
                
                text = candidate.content.parts[0].text
                
                if not text or not text.strip():
                    raise AIServiceError(
                        "Generated text is empty",
                        error_code="EMPTY_TEXT"
                    )
                
                logger.debug(f"✅ Gemini response received ({len(text)} chars)")
                return text
                
            except AIServiceError:
                # Re-raise AIServiceError directly
                raise
                
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt}/{self.max_retries} failed: {type(e).__name__}: {str(e)}"
                )
                
                # Don't retry on certain errors
                if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                    raise AIServiceError(
                        f"Gemini API quota/rate limit exceeded: {str(e)}",
                        error_code="QUOTA_EXCEEDED"
                    )
                
                if attempt == self.max_retries:
                    logger.error(f"❌ Gemini AI failed after {attempt} attempts")
                    raise AIServiceError(
                        f"AI service failed after {attempt} retries: {str(last_exception)}",
                        error_code="GEMINI_UNAVAILABLE"
                    )
                
                # Exponential backoff
                await asyncio.sleep(delay)
                delay *= 2

    async def test_connection(self) -> bool:
        """
        Test connectivity to Gemini AI
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            test_text = await self.generate_text(
                "Hello", 
                temperature=0.0, 
                max_tokens=10
            )
            return len(test_text) > 0
        except AIServiceError as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection test: {e}")
            return False


# Singleton instance management
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """
    Get or create singleton GeminiService instance
    
    Returns:
        GeminiService instance
    """
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service


__all__ = ["get_gemini_service", "GeminiService"]
"""
Google Gemini AI Service
Wrapper for Gemini Pro API (FREE!)
"""
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Handles all Gemini AI interactions"""
    
    def __init__(self):
        """Initialize Gemini with API key"""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Use the model name without API version issues
        model_name = settings.GEMINI_MODEL
        # Try different model name formats
        if "gemini-1.5" in model_name:
            model_name = "models/" + model_name
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"✅ Gemini AI initialized: {model_name}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_text(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text using Gemini
        
        Args:
            prompt: The input prompt
            temperature: Creativity (0.0-1.0). Lower = more focused
            max_tokens: Max response length
            
        Returns:
            Generated text
        """
        try:
            # Use settings defaults if not provided
            temp = temperature if temperature is not None else settings.GEMINI_TEMPERATURE
            max_tok = max_tokens if max_tokens is not None else settings.MAX_OUTPUT_TOKENS
            
            # Generate
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temp,
                    max_output_tokens=max_tok,
                )
            )
            
            # Extract text - handle different response formats
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
            elif hasattr(response, 'parts') and response.parts:
                return response.parts[0].text.strip()
            elif hasattr(response, 'candidates') and response.candidates:
                if len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        if len(candidate.content.parts) > 0:
                            return candidate.content.parts[0].text.strip()
            
            logger.error(f"Unexpected response format: {response}")
            raise Exception("Empty or invalid response from Gemini")
                
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise Exception(f"AI generation failed: {str(e)}")
    
    async def analyze_with_structure(
        self,
        prompt: str,
        structure_instructions: str
    ) -> str:
        """
        Generate structured output (e.g., JSON)
        
        Args:
            prompt: Main prompt
            structure_instructions: How to format output
            
        Returns:
            Structured text
        """
        full_prompt = f"""
{prompt}

{structure_instructions}

IMPORTANT: Return ONLY the requested format, no additional text.
"""
        return await self.generate_text(full_prompt, temperature=0.1)
    
    def test_connection(self) -> bool:
        """Test if Gemini API is working"""
        try:
            # Simple test with minimal prompt
            response = self.model.generate_content("Say OK")
            return response.text and len(response.text) > 0
        except Exception as e:
            logger.error(f"Gemini connection test failed: {str(e)}")
            return False


# Global instance
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create Gemini service singleton"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
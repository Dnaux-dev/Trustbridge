"""
TrustBridge AI-Legal Engine Configuration
Enhanced with validation and type safety
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache
from typing import List
import sys
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables with validation"""

    # App Info
    APP_NAME: str = Field(
        "TrustBridge AI-Legal Engine", 
        description="Application name"
    )
    APP_VERSION: str = Field(
        "1.0.0", 
        description="Application version"
    )
    DEBUG: bool = Field(
        True, 
        description="Enable debug mode"
    )
    LOG_LEVEL: str = Field(
        "INFO", 
        description="Logging level"
    )
    ENVIRONMENT: str = Field(
        "development",
        description="Environment name (development/staging/production)"
    )

    # Google Gemini API
    GEMINI_API_KEY: str = Field(
        ..., 
        description="Google Gemini API key"
    )
    GEMINI_MODEL: str = Field(
        "gemini-2.0-flash-exp", 
        description="Gemini model name"
    )
    GEMINI_TEMPERATURE: float = Field(
        0.3, 
        description="Sampling temperature for AI (0.0 deterministic, 2.0 creative)"
    )
    MAX_OUTPUT_TOKENS: int = Field(
        8192, 
        description="Max tokens per AI generation"
    )

    # Security
    API_SECRET_KEY: str = Field(
        ..., 
        description="Secret key for API security"
    )
    ALLOWED_ORIGINS: str = Field(
        "http://localhost:3000,http://localhost:8000", 
        description="Comma-separated list of allowed CORS origins"
    )

    # Compliance Scoring Thresholds
    MIN_COMPLIANCE_SCORE: int = Field(
        70, 
        description="Minimum compliance score to avoid HIGH RISK"
    )
    MED_COMPLIANCE_SCORE: int = Field(
        85, 
        description="Threshold for GOOD compliance"
    )

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(
        100, 
        description="API requests limit per minute"
    )
    RATE_LIMIT_POLICY_ANALYSIS: str = Field(
        "10/hour",
        description="Rate limit for policy analysis endpoint"
    )
    RATE_LIMIT_QUICK_CHECK: str = Field(
        "30/hour",
        description="Rate limit for quick compliance check"
    )

    # Validators
    @field_validator('GEMINI_API_KEY')
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate Gemini API key format"""
        if not v or v == "your-api-key-here" or v == "your-gemini-api-key-here":
            raise ValueError(
                "GEMINI_API_KEY must be set to a valid API key. "
                "Get one at: https://makersuite.google.com/app/apikey"
            )
        if len(v) < 20:
            raise ValueError("GEMINI_API_KEY appears to be invalid (too short)")
        return v
    
    @field_validator('API_SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate API secret key strength"""
        if not v or v == "your-secret-key-here":
            raise ValueError("API_SECRET_KEY must be set to a secure value")
        if len(v) < 32:
            raise ValueError(
                "API_SECRET_KEY must be at least 32 characters for security"
            )
        return v
    
    @field_validator('GEMINI_TEMPERATURE')
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature range"""
        if not 0.0 <= v <= 2.0:
            raise ValueError("GEMINI_TEMPERATURE must be between 0.0 and 2.0")
        return v
    
    @field_validator('MAX_OUTPUT_TOKENS')
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        """Validate max output tokens"""
        if v < 100:
            raise ValueError("MAX_OUTPUT_TOKENS must be at least 100")
        if v > 32000:
            raise ValueError("MAX_OUTPUT_TOKENS cannot exceed 32000")
        return v
    
    @field_validator('ALLOWED_ORIGINS')
    @classmethod
    def validate_origins(cls, v: str) -> str:
        """Validate CORS origins format"""
        if not v.strip():
            raise ValueError("ALLOWED_ORIGINS cannot be empty")
        
        origins = [o.strip() for o in v.split(",")]
        for origin in origins:
            if not origin.startswith(("http://", "https://")):
                raise ValueError(
                    f"Invalid origin '{origin}': must start with http:// or https://"
                )
        return v
    
    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"LOG_LEVEL must be one of: {', '.join(valid_levels)}"
            )
        return v_upper
    
    @field_validator('ENVIRONMENT')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment name"""
        valid_envs = ["development", "staging", "production"]
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(
                f"ENVIRONMENT must be one of: {', '.join(valid_envs)}"
            )
        return v_lower

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origins string to list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT == "development"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance with validation error handling
    
    Returns:
        Settings instance
        
    Raises:
        SystemExit: If configuration is invalid
    """
    try:
        settings = Settings()
        logger.info("✅ Configuration loaded successfully")
        return settings
    except Exception as e:
        print(f"\n❌ Configuration Error:\n{str(e)}\n")
        print("Please check your .env file and ensure all required variables are set correctly.")
        print("See .env.example for reference.\n")
        sys.exit(1)


# Global singleton instance
settings = get_settings()

__all__ = ["settings", "get_settings"]
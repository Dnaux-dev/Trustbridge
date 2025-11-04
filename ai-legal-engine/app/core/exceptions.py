"""
Custom exception classes for TrustBridge AI-Legal Engine
Provides structured error handling with error codes
"""


class ServiceError(Exception):
    """
    Base exception class for all service-related errors.
    Allows optional error code and message.
    """
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "SERVICE_ERROR"

    def __str__(self):
        return f"[{self.error_code}] {self.message}"
    
    def to_dict(self):
        """Convert exception to dictionary for API responses"""
        return {
            "error": self.error_code,
            "message": self.message
        }


class AIServiceError(ServiceError):
    """
    Exception raised when the AI backend (Google Gemini) returns an error or fails.
    
    Common error codes:
    - GEMINI_INIT_FAILED: Initialization failure
    - GEMINI_UNAVAILABLE: Service unavailable after retries
    - INVALID_PROMPT: Empty or invalid prompt
    - EMPTY_RESPONSE: No response from AI
    - SAFETY_BLOCK: Content blocked by safety filters
    - QUOTA_EXCEEDED: API quota exceeded
    - INVALID_AI_RESPONSE: Invalid JSON or malformed response
    """
    def __init__(self, message: str, error_code: str = "AI_SERVICE_ERROR"):
        super().__init__(message, error_code)


class ValidationError(ServiceError):
    """
    Exception to raise when input validation fails (beyond Pydantic validation).
    Use for additional domain validation rules.
    
    Common error codes:
    - INVALID_INPUT: General input validation failure
    - DOCUMENT_TOO_LARGE: Document exceeds size limits
    - INVALID_FORMAT: Incorrect data format
    """
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message, error_code)


class ExternalAPIError(ServiceError):
    """
    Exception raised when third-party APIs (other than AI) fail or return unexpected results.
    
    Common error codes:
    - API_UNAVAILABLE: External API is down
    - API_TIMEOUT: Request timed out
    - API_RATE_LIMIT: Rate limit exceeded
    """
    def __init__(self, message: str, error_code: str = "EXTERNAL_API_ERROR"):
        super().__init__(message, error_code)


class NotFoundError(ServiceError):
    """
    Exception for entity not found situations.
    
    Common error codes:
    - RESOURCE_NOT_FOUND: Requested resource doesn't exist
    - ANALYSIS_NOT_FOUND: Analysis ID not found
    """
    def __init__(self, message: str, error_code: str = "NOT_FOUND"):
        super().__init__(message, error_code)


class UnauthorizedError(ServiceError):
    """
    Exception for authorization failures.
    
    Common error codes:
    - UNAUTHORIZED: No authentication provided
    - FORBIDDEN: Insufficient permissions
    - INVALID_TOKEN: Authentication token is invalid
    """
    def __init__(self, message: str, error_code: str = "UNAUTHORIZED"):
        super().__init__(message, error_code)


class RateLimitError(ServiceError):
    """
    Exception for rate limiting violations.
    
    Common error codes:
    - RATE_LIMIT_EXCEEDED: Too many requests
    """
    def __init__(self, message: str, error_code: str = "RATE_LIMIT_EXCEEDED"):
        super().__init__(message, error_code)


__all__ = [
    "ServiceError",
    "AIServiceError",
    "ValidationError",
    "ExternalAPIError",
    "NotFoundError",
    "UnauthorizedError",
    "RateLimitError"
]
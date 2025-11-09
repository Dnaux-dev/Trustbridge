"""
TrustBridge AI-Legal Engine
Main FastAPI Application

Using Google Gemini (FREE!) - No AWS, No C++, No Problems! 🚀
"""
from fastapi.responses import JSONResponse
from datetime import datetime
from app.core.exceptions import RateLimitError, ValidationError, AIServiceError
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

import logging
import time
from contextlib import asynccontextmanager

from pydantic import ValidationError  # Use pydantic ValidationError, not pydantic_core
from app.core.config import settings
from app.api.routes import router as api_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("="*60)
    logger.info("🏛️  TrustBridge AI-Legal Engine Starting...")
    logger.info(f"📋 Version: {settings.APP_VERSION}")
    logger.info(f"🤖 AI Model: {settings.GEMINI_MODEL}")
    logger.info(f"🔧 Debug Mode: {settings.DEBUG}")
    logger.info("="*60)
    
    # Test Gemini connection
    try:
        from app.services.gemini_service_v2 import get_gemini_service
        gemini = get_gemini_service()
        if await gemini.test_connection():
            logger.info("✅ Gemini AI: Connected")
        else:
            logger.warning("⚠️  Gemini AI: Connection test failed")
    except Exception as e:
        logger.error(f"❌ Gemini AI: Failed to initialize - {str(e)}")
    
    yield

    # Shutdown
    logger.info("👋 Shutting down TrustBridge AI-Legal Engine...")

# Create FastAPI app with lifespan context
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    🏛️ **TrustBridge AI-Legal Engine**

    AI-powered NDPR/GDPR compliance analysis using Google Gemini.

    **Key Features:**
    - 📋 Privacy Policy Analysis
    - ⚖️  Citizen Action Validation
    - 🔍 Quick Compliance Checks
    - 🤖 AI-Generated Legal Fixes

    **Powered by:** Google Gemini Pro (FREE!)
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

@app.exception_handler(RateLimitError)
async def rate_limit_handler(request: Request, exc: RateLimitError):
    """Handle rate limit errors"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": exc.message,
            "retry_after": 60,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(AIServiceError)
async def ai_service_error_handler(request: Request, exc: AIServiceError):
    """Handle AI service errors"""
    return JSONResponse(
        status_code=503,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# CORS Middleware
# If ALLOW_ALL_ORIGINS is set, allow '*' for CORS. Otherwise use the configured list.
cors_origins = ["*"] if getattr(settings, 'ALLOW_ALL_ORIGINS', False) else settings.allowed_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = str(int(process_time))
    return response

# Include API routes
app.include_router(api_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "service": "TrustBridge AI-Legal Engine",
        "version": settings.APP_VERSION,
        "status": "operational",
        "ai_model": settings.GEMINI_MODEL,
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "health": "/api/v1/health",
            "analyze_policy": "/api/v1/analyze/policy",
            "validate_action": "/api/v1/validate/action",
            "quick_check": "/api/v1/check/compliance"
        }
    }

# Exception handler for validation errors
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting server...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )

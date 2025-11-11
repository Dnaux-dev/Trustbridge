import os
from dotenv import load_dotenv

# Load environment variables from .env (if present) so uvicorn/process picks them up automatically
load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://127.0.0.1:27017/trustbridge_fastapi')
JWT_SECRET = os.getenv('JWT_SECRET', 'dev-fastapi-secret')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
INTERNAL_TOKEN = os.getenv('INTERNAL_TOKEN', 'internal-secret-token')
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '')  # comma-separated list; if empty, allow wildcard without credentials

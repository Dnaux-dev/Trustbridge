from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer
from typing import Optional
from .config import JWT_SECRET, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, INTERNAL_TOKEN
from . import db as db_module
from bson import ObjectId

# Use pbkdf2_sha256 to avoid bcrypt's 72-byte password length limitation and
# to avoid importing bcrypt-specific handlers which may enforce native limits.
pwd_context = CryptContext(schemes=['pbkdf2_sha256'], deprecated='auto')
security = HTTPBearer()

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(security)):
    credentials = token.credentials
    try:
        payload = jwt.decode(credentials, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = payload.get('sub') or payload.get('id')
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid user id in token')
    user = await db_module.db['users'].find_one({'_id': oid})
    # If storing ObjectId, you might need to convert; here we assume id stored as str
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    return user

def require_role(*allowed):
    async def role_checker(user: dict = Depends(get_current_user)):
        if user.get('role') in allowed or 'admin' in allowed and user.get('role') == 'admin':
            return user
        if user.get('role') not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Forbidden')
        return user
    return role_checker

async def internal_only(x_internal_token: Optional[str] = Header(None)):
    if x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid internal token')

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = 'citizen'
    company: Optional[str]

class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'

class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    company: Optional[str]

class Company(BaseModel):
    id: Optional[str]
    name: str
    description: Optional[str]
    contactEmail: Optional[EmailStr]
    policies: Optional[str]

class ActionIn(BaseModel):
    type: str
    details: Optional[dict]
    companyId: Optional[str]

class AIResult(BaseModel):
    advice: str
    risk: str
    suggestions: List[str] = []
    timestamp: Optional[datetime]

class LedgerEntryOut(BaseModel):
    id: str
    action: Any
    actor: str
    actorRole: str
    actionType: str
    company: Optional[str]
    timestamp: datetime
    aiReport: Any
    raw: Optional[dict]

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime

class UserCreate(BaseModel):
    """Payload to create a new user."""
    name: str = Field(..., description="Full name of the user", example="Alice Doe")
    email: EmailStr = Field(..., description="User email address", example="alice@example.com")
    password: str = Field(..., description="Plain-text password (will be hashed)", example="sup3rsecret")
    role: Optional[str] = Field('citizen', description="Role (citizen, business, admin)", example="citizen")
    company: Optional[str] = Field(None, description="Optional company id if the user belongs to a company", example=None)

class Token(BaseModel):
    """Authentication token returned after login."""
    access_token: str = Field(..., description="JWT access token", example="eyJhbGciOi...")
    token_type: str = Field('bearer', description="Token type", example='bearer')

class UserOut(BaseModel):
    id: str = Field(..., description="User id", example="6532f1a...")
    name: str = Field(..., description="Full name", example="Alice Doe")
    email: EmailStr = Field(..., description="Email address", example="alice@example.com")
    role: str = Field(..., description="Role", example="citizen")
    company: Optional[str] = Field(None, description="Company id if any", example=None)

class Company(BaseModel):
    id: Optional[str] = Field(None, description="Company id", example="5f8d0d55")
    name: str = Field(..., description="Company name", example="Acme Ltd")
    description: Optional[str] = Field(None, description="Short description of the company", example="Payments startup")
    contactEmail: Optional[EmailStr] = Field(None, description="Contact email", example="dpo@acme.example")
    policies: Optional[str] = Field(None, description="Policy text or URL", example="https://acme.example/privacy")

class ActionIn(BaseModel):
    """Request payload for recording an action from a user."""
    type: str = Field(..., description="Action type identifier", example="revoke_consent")
    details: Optional[dict] = Field(None, description="Arbitrary action details", example={"text":"I withdraw consent","data_types":["email"]})
    companyId: Optional[str] = Field(None, description="Optional company id the action targets", example="5f8d0d55")

class AIResult(BaseModel):
    advice: str = Field(..., description="Plain language advice from the AI", example="Revocation noted; notify processors and delete data.")
    risk: str = Field(..., description="Risk level (low/medium/high)", example="low")
    suggestions: List[str] = Field([], description="Actionable suggestions", example=["Confirm deletion schedule","Notify processors"]) 
    timestamp: Optional[datetime] = Field(None, description="AI response timestamp", example="2025-11-10T10:00:00Z")

class LedgerEntryOut(BaseModel):
    id: str = Field(..., description="Ledger entry id", example="655a1b2c")
    action: Any = Field(..., description="The stored action document or reference")
    actor: str = Field(..., description="Actor id", example="6532f1a...")
    actorRole: str = Field(..., description="Actor role", example="citizen")
    actionType: str = Field(..., description="Action type", example="revoke_consent")
    company: Optional[str] = Field(None, description="Company id", example="5f8d0d55")
    timestamp: datetime = Field(..., description="When the action was recorded", example="2025-11-10T10:00:00Z")
    aiReport: Any = Field(None, description="AI analysis attached to this ledger entry")
    raw: Optional[dict] = Field(None, description="Raw request or metadata", example={"source":"recordAction"})


class RecordActionResponse(BaseModel):
    actionId: str = Field(..., description="Created action id", example="655a1b2c")
    ai: Optional[AIResult] = Field(None, description="AI analysis result (if any)")


class ActionOut(BaseModel):
    """Stored action document returned by the actions endpoint."""
    id: str = Field(..., description="Action id", example="655a1b2c")
    actor: Optional[str] = Field(None, description="Actor id", example="6532f1a...")
    actorRole: Optional[str] = Field(None, description="Actor role", example="citizen")
    type: str = Field(..., description="Action type", example="revoke_consent")
    details: Optional[dict] = Field(None, description="Action details", example={"text":"I withdraw consent"})
    company: Optional[str] = Field(None, description="Company id if any", example="5f8d0d55")
    createdAt: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-11-10T10:00:00Z")

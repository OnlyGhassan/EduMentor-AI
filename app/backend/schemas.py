from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from uuid import UUID

# ---------- Auth ----------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str
    exp: int

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: UUID
    created_at: datetime

# ---------- Documents / Messages ----------
class DocumentBase(BaseModel):
    filename: str
    content: str

class DocumentOut(DocumentBase):
    id: UUID

class MessageBase(BaseModel):
    role: str
    type: str
    content: str
    created_at: datetime

class MessageOut(MessageBase):
    id: UUID

# ---------- Sessions ----------
class SessionCreate(BaseModel):
    name: Optional[str] = "Untitled Session"

class SessionOut(BaseModel):
    id: UUID
    name: str
    created_at: datetime

class SessionDetail(SessionOut):
    documents: List[DocumentOut] = []
    messages: List[MessageOut] = []

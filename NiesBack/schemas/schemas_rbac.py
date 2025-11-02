from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import List, Optional
from models.models_rbac import UserStatus

class UserCreate(BaseModel):
    name: str
    cpf: str
    email: EmailStr
    phone: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    password: str = Field(min_length=6)

class UserOut(BaseModel):
    id: int
    name: str
    cpf: str
    email: EmailStr
    phone: Optional[str]
    status: UserStatus
    is_admin: bool
    class Config:
        from_attributes = True

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    refresh_token: str

class RefreshIn(BaseModel):
    refresh_token: str
    

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class UserGroupOut(BaseModel):
    name: str
    description: Optional[str]
    report_ids: List[str] = []
    class Config:
        from_attributes = True

class UserGroupCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    report_ids: List[str] = []  # permissões iniciais (opcional)

class ReportIdsIn(BaseModel):
    report_ids: List[str]

from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional, Literal
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

class GroupOutRBAC(BaseModel):
    id: int
    name: str
    description: Optional[str]
    class Config:
        from_attributes = True

class GroupMemberIn(BaseModel):
    user_id: int

class GroupReportPermissionIn(BaseModel):
    report_id: str  # String(64) para casar com reports.id

# roles/permissions
class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionCreate(BaseModel):
    code: str
    description: Optional[str] = None

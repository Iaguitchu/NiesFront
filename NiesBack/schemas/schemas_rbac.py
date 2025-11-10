from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import List, Optional,Literal
from models.models_rbac import UserStatus

class UserCreate(BaseModel):
    name: str
    cpf: str
    email: EmailStr
    phone: Optional[str] = None
    status: Literal["approved", "pending"] = "pending"
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    group_ids: List[str] = Field(default_factory=list)

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
    report_ids: List[str] = []

class ReportIdsIn(BaseModel):
    report_ids: List[str]


class ReportGroupCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    is_public: bool = True

class ReportSubgroupCreate(BaseModel):
    name: str = Field(min_length=1)
    parent_id: str
    description: str | None = None
    is_public: bool = True

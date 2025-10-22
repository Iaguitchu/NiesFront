# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.models_rbac import User, UserStatus
from schemas.schemas_rbac import UserCreate, LoginIn, TokenOut, UserOut
from services.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(400, "Email already registered")
    if db.query(User).filter(User.cpf == user_in.cpf).first():
        raise HTTPException(400, "CPF already registered")
    u = User(
        name=user_in.name,
        cpf=user_in.cpf,
        email=user_in.email,
        phone=user_in.phone,
        valid_from=user_in.valid_from,
        valid_to=user_in.valid_to,
        password_hash=hash_password(user_in.password),
        status=UserStatus.pending,
        is_admin=False,
    )
    db.add(u); db.commit(); db.refresh(u)
    return u

@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == data.email).first()
    if not u or not verify_password(data.password, u.password_hash):
        raise HTTPException(401, "Invalid credentials")
    if u.status != UserStatus.approved:
        raise HTTPException(403, "User not approved")
    return TokenOut(access_token=create_access_token(u.id, u.is_admin))

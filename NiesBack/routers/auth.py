# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from db import get_db
from models.models_rbac import User, UserStatus
from schemas.schemas_rbac import UserCreate, LoginIn, TokenOut, UserOut, RefreshIn
from services.security import *
from datetime import timedelta
from fastapi.responses import HTMLResponse
from core.templates import templates
router = APIRouter(prefix="/auth", tags=["auth"])

ACCESS_EXPIRES = timedelta(minutes=15)
REFRESH_EXPIRES = timedelta(days=7)

def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()

@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    email = _normalize_email(user_in.email)
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "Email already registered")
    if db.query(User).filter(User.cpf == user_in.cpf).first():
        raise HTTPException(400, "CPF already registered")

    u = User(
        name=user_in.name.strip(),
        cpf=user_in.cpf.strip(),
        email=email,
        phone=(user_in.phone or "").strip(),
        valid_from=user_in.valid_from,
        valid_to=user_in.valid_to,
        password_hash=hash_password(user_in.password),
        status=UserStatus.pending,  # ficará pendente até aprovação
        is_admin=False,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    invalid_err = HTTPException(401, "Invalid email or password")

    u = db.query(User).filter(User.email == _normalize_email(data.email)).first()
    if not u or not verify_password(data.password, u.password_hash):
        raise invalid_err

    if u.status != UserStatus.approved:
        raise HTTPException(403, "User not approved")

    access = create_access_token(sub=str(u.id), is_admin=u.is_admin, expires_delta=ACCESS_EXPIRES)
    refresh, jti = create_refresh_token(sub=str(u.id), expires_delta=REFRESH_EXPIRES)

    # registra o jti do refresh (para poder revogar depois)
    store_refresh_jti(user_id=str(u.id), jti=jti, exp_seconds=int(REFRESH_EXPIRES.total_seconds()))

    return TokenOut(access_token=access, refresh_token=refresh)

@router.post("/refresh", response_model=TokenOut)
def refresh_token(payload: TokenOut, db: Session = Depends(get_db)):
    """
    Recebe o refresh_token e entrega um novo access_token (e um novo refresh opcional).
    """
    if not payload.refresh_token:
        raise HTTPException(400, "Missing refresh_token")

    claims = decode_token_safely(payload.refresh_token, verify_type="refresh")
    if not claims:
        raise HTTPException(401, "Invalid refresh token")

    jti = claims.get("jti")
    print('jti',jti)
    sub = claims.get("sub")
    print('jti',sub)
    if not sub or not jti or is_refresh_jti_revoked(jti):
        raise HTTPException(401, "Invalid refresh token")

    # rotate refresh: revogar o antigo e emitir novo
    revoke_refresh_jti(jti)

    u = db.query(User).get(sub)
    if not u or u.status != UserStatus.approved:
        raise HTTPException(403, "User not allowed")

    new_access = create_access_token(sub=str(u.id), is_admin=u.is_admin, expires_delta=ACCESS_EXPIRES)
    new_refresh, new_jti = create_refresh_token(sub=str(u.id), expires_delta=REFRESH_EXPIRES)
    store_refresh_jti(user_id=str(u.id), jti=new_jti, exp_seconds=int(REFRESH_EXPIRES.total_seconds()))

    return TokenOut(access_token=new_access, refresh_token=new_refresh)

@router.post("/logout")
def logout(payload: RefreshIn):
    """
    Opcional: o front envia o refresh_token atual para invalidar.
    """
    if not payload.refresh_token:
        return {"ok": True}

    claims = decode_token_safely(payload.refresh_token, verify_type="refresh")
    if claims and claims.get("jti"):
        revoke_refresh_jti(claims["jti"])
    return {"ok": True}

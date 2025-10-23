from core.settings import settings
from db import get_db
from models.models_rbac import User, UserStatus
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends, Header

import os, time, uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from jose import jwt, JWTError
from passlib.context import CryptContext

SECRET_KEY = settings.SECRET_KEY
ALGO = "HS256"

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Simples KV para refresh JTI (troque por Redis em prod)
_REVOKED = set()
_ACTIVE = {}

def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_ctx.verify(password, password_hash)
    except Exception:
        return False

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _exp(delta: timedelta) -> int:
    return int((_now() + delta).timestamp())

def create_access_token(sub: str, is_admin: bool, expires_delta: timedelta) -> str:
    claims = {
        "sub": sub,
        "is_admin": is_admin,
        "type": "access",
        "exp": _exp(expires_delta),
    }
    return jwt.encode(claims, SECRET_KEY, algorithm=ALGO)

def create_refresh_token(sub: str, expires_delta: timedelta) -> Tuple[str, str]:
    jti = str(uuid.uuid4())
    claims = {
        "sub": sub,
        "type": "refresh",
        "jti": jti,
        "exp": _exp(expires_delta),
    }
    token = jwt.encode(claims, SECRET_KEY, algorithm=ALGO)
    return token, jti

def decode_token_safely(token: str, verify_type: Optional[str] = None) -> Optional[dict]:
    try:
        claims = jwt.decode(token, SECRET_KEY, algorithms=[ALGO])
        if verify_type and claims.get("type") != verify_type:
            return None
        return claims
    except JWTError:
        return None

def store_refresh_jti(user_id: str, jti: str, exp_seconds: int):
    # Em produção use Redis: SETEX jti -> user_id
    _ACTIVE[jti] = (user_id, int(time.time()) + exp_seconds)

def revoke_refresh_jti(jti: str):
    _REVOKED.add(jti)
    if jti in _ACTIVE:
        del _ACTIVE[jti]

def is_refresh_jti_revoked(jti: str) -> bool:
    if jti in _REVOKED:
        return True
    # expire local
    tu = _ACTIVE.get(jti)
    if not tu:
        return True  # não conhecido = inválido
    _, exp = tu
    if time.time() > exp:
        del _ACTIVE[jti]
        return True
    return False


def get_current_user_optional(
        db: Session = Depends(get_db), authorization: Optional[str] = Header(default=None, alias="Authorization"),) -> Optional[User]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    try:
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGO])
        if data.get("type") != "access":
            raise HTTPException(401, "Invalid token type")

        uid = data.get("sub")
        if uid is None:
            raise HTTPException(401, "Invalid token")

        user = db.get(User, int(uid))
        if not user or user.status != UserStatus.approved:
            raise HTTPException(403, "User not approved")

        return user
    except JWTError:
        raise HTTPException(401, "Invalid token")

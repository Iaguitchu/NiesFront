from core.settings import settings
from db import get_db
from models.models_rbac import User, UserStatus
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends, Header, Request, Response

from datetime import datetime, timedelta, timezone
from typing import Optional, Annotated
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
from starlette import status

ACCESS_EXPIRES = timedelta(minutes=1)
REFRESH_EXPIRES = timedelta(days=7)
SECRET_KEY = settings.SECRET_KEY
ALGO = "HS256"

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

def create_refresh_token(sub: str, expires_delta: timedelta) -> str:
    claims = {
        "sub": sub,
        "type": "refresh",
        "exp": _exp(expires_delta),
    }
    return jwt.encode(claims, SECRET_KEY, algorithm=ALGO)

def decode_token_safely(token: str, verify_type: Optional[str] = None) -> Optional[dict]:
    try:
        claims = jwt.decode(token, SECRET_KEY, algorithms=[ALGO])
        if verify_type and claims.get("type") != verify_type:
            return None
        return claims
    except JWTError:
        return None
    
    
    
def get_current_user_optional(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> Optional[User]:
    token: Optional[str] = None

    # 1) tenta Authorization: Bearer <token>
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()

    # 2) se não veio no header, tenta cookie
    if not token:
        token = request.cookies.get("access_token")

    # ---------- CASO 0: não há access_token ----------
    if not token:
        # tenta renovar usando apenas o refresh_token
        rt = request.cookies.get("refresh_token")
        claims = decode_token_safely(rt, verify_type="refresh") if rt else None
        if not claims:
            return None

        uid = claims.get("sub")
        if not uid:
            return None

        user = db.get(User, int(uid))
        if not user or user.status != UserStatus.approved:
            return None

        # emite novo access e renova cookie
        new_access = create_access_token(
            sub=str(user.id),
            is_admin=user.is_admin,
            expires_delta=ACCESS_EXPIRES,
        )
        response.set_cookie(
            key="access_token",
            value=new_access,
            httponly=True,
            secure=False,      # True em produção (HTTPS)
            samesite="lax",
            path="/",
            max_age=int(ACCESS_EXPIRES.total_seconds()),
        )
        return user

    # ---------- CASO 1: há access_token ----------
    try:
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGO])
        if data.get("type") != "access":
            return None

        uid = data.get("sub")
        if not uid:
            return None

        user = db.get(User, int(uid))
        if not user or user.status != UserStatus.approved:
            return None

        return user

    except ExpiredSignatureError:
        # access expirou → tenta refresh
        rt = request.cookies.get("refresh_token")
        claims = decode_token_safely(rt, verify_type="refresh") if rt else None
        if not claims:
            return None

        uid = claims.get("sub")
        if not uid:
            return None

        user = db.get(User, int(uid))
        if not user or user.status != UserStatus.approved:
            return None

        new_access = create_access_token(
            sub=str(user.id),
            is_admin=user.is_admin,
            expires_delta=ACCESS_EXPIRES,
        )
        response.set_cookie(
            key="access_token",
            value=new_access,
            httponly=True,
            secure=False,
            samesite="lax",
            path="/",
            max_age=int(ACCESS_EXPIRES.total_seconds()),
        )
        return user

    except JWTError:
        # token inválido → tenta refresh como último recurso
        rt = request.cookies.get("refresh_token")
        claims = decode_token_safely(rt, verify_type="refresh") if rt else None
        if not claims:
            return None

        uid = claims.get("sub")
        if not uid:
            return None

        user = db.get(User, int(uid))
        if not user or user.status != UserStatus.approved:
            return None

        new_access = create_access_token(
            sub=str(user.id),
            is_admin=user.is_admin,
            expires_delta=ACCESS_EXPIRES,
        )
        response.set_cookie(
            key="access_token",
            value=new_access,
            httponly=True,
            secure=False,
            samesite="lax",
            path="/",
            max_age=int(ACCESS_EXPIRES.total_seconds()),
        )
        return user
    
def require_admin(user: User | None = Depends(get_current_user_optional)) -> User:
    if not user:
        # 303 + Location faz o redirect
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/auth/login"},
        )
    if not getattr(user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/"},
        )
    return user


def get_current_user(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> User:
    user = get_current_user_optional(request, response, db, authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

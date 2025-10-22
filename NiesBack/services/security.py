# security.py
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, Depends
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from core.settings import settings

from db import get_db
from models.models_rbac import User, UserStatus

# SECRET_KEY = "troque-por-env"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8 # 8 horas

pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],  # bcrypt_sha256 para novos hashes
    deprecated="auto",
)

def hash_password(p: str) -> str:
    return pwd_context.hash(p)

def verify_password(p: str, phash: str) -> bool:
    return pwd_context.verify(p, phash)

def create_access_token(sub: int, is_admin: bool) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": sub, "adm": is_admin, "exp": exp}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM) 

def get_current_user_optional(
    db: Session = Depends(get_db),
    authorization: Optional[str] = None
) -> Optional[User]:
    """Retorna None se não houver Bearer; se houver, valida e carrega o usuário aprovado."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    try:
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        uid = data.get("sub")
        if uid is None:
            raise HTTPException(401, "Invalid token")
        user = db.query(User).get(uid)
        if not user or user.status != UserStatus.approved:
            raise HTTPException(403, "User not approved")
        return user
    except JWTError:
        raise HTTPException(401, "Invalid token")

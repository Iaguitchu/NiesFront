from datetime import datetime, timedelta, timezone
import secrets
from sqlalchemy.orm import Session
from sqlalchemy import select
from models.models_rbac import PasswordReset, User
from passlib.context import CryptContext
from core.settings import settings


_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return _pwd.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)

def _utcnow():
    return datetime.now()

def create_password_reset(db: Session, user: User) -> tuple[str, str]:
    """
    Cria um reset e retorna (reset_id, raw_token) para montar o link.
    """
    raw_token = secrets.token_urlsafe(32)
    pr = PasswordReset(
        user_id=user.id,
        token_hash=hash_password(raw_token),
        expires_at=_utcnow() + timedelta(seconds=settings.PASSWORD_RESET_EXPIRES_SECONDS),
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pr.reset_id, raw_token

def get_valid_password_reset(db: Session, reset_id: str, token: str) -> PasswordReset | None:
    pr = db.execute(
        select(PasswordReset).where(PasswordReset.reset_id == reset_id)
    ).scalar_one_or_none()
    if not pr:
        return None
    if pr.used_at is not None:
        return None
    if pr.expires_at < _utcnow():
        return None
    if not verify_password(token, pr.token_hash):
        return None
    return pr

def mark_used(db: Session, pr: PasswordReset) -> None:
    pr.used_at = _utcnow()
    db.add(pr)
    db.commit()

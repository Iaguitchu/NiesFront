from core.email import send_email
from core.settings import settings
from db import get_db

from models.models_rbac import User
from models.password_reset import PasswordReset
from schemas.auth_reset import ForgotVerifyIn, ResetPasswordIn
from services.security import hash_password
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from datetime import datetime, timedelta, timezone
import secrets

RESET_CODE_EXPIRY_MINUTES = 15

def send_reset_code(email: str, db: Session):
    email_norm = (email or "").strip().lower()
    generic = {"message": "Se o e-mail existir, enviaremos um código de redefinição."}

    user = db.query(User).filter(User.email == email_norm).first()
    if not user:
        # não revelar existência
        return generic

    # (opcional) invalidar resets anteriores abertos
    db.query(PasswordReset).filter(
        PasswordReset.user_id == user.id,
        PasswordReset.used == False
    ).update({"used": True})

    code = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_CODE_EXPIRY_MINUTES)

    rec = PasswordReset(
        user_id=user.id,
        code=code,
        expires_at=expires_at,
        used=False
    )
    db.add(rec)
    db.commit()

    send_email(
        to=email_norm,
        subject="Seu código de redefinição de senha",
        body=f"Seu código de redefinição de senha é: {code}. Ele expira em {RESET_CODE_EXPIRY_MINUTES} minutos."
    )

    return generic


from __future__ import annotations
from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, DateTime, Boolean, Integer, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship


from models.models import Base 

class PasswordReset(Base):
    __tablename__ = "password_resets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    code: Mapped[str] = mapped_column(String(6), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="password_resets")

    __table_args__ = (
        Index("ix_pr_user_created", "user_id", "created_at"),
        Index("ix_pr_user_used", "user_id", "used"),
    )

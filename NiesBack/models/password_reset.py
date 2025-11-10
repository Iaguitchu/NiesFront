# from models.models import Base 

# from sqlalchemy import String, Integer, DateTime, ForeignKey
# from sqlalchemy.orm import Mapped, mapped_column, relationship
# from datetime import datetime
# import uuid

# class PasswordReset(Base):
#     __tablename__ = "password_resets"
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
#     reset_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
#     user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
#     token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
#     expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
#     used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

#     user: Mapped["User"] = relationship(back_populates="password_resets")


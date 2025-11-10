from datetime import datetime, date
from sqlalchemy import (
    String, Boolean, Integer, Date, DateTime, Enum, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from models.models import Base
import uuid



# -----------------------------------------
# Estados do usuário
# -----------------------------------------
class UserStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    blocked = "blocked"

# -----------------------------------------
# Usuários
# -----------------------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    cpf: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))

    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.pending, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    group_memberships: Mapped[list["UserGroupMember"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    roles: Mapped[list["UserRole"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    password_resets: Mapped[list["PasswordReset"]] = relationship("PasswordReset", back_populates="user",cascade="all, delete-orphan",)

# -----------------------------------------
# Grupos de usuários (para VISUALIZAÇÃO de relatórios)
# -----------------------------------------
class UserGroup(Base):
    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(300))

    members: Mapped[list["UserGroupMember"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    report_permissions: Mapped[list["GroupReportPermission"]] = relationship(back_populates="group", cascade="all, delete-orphan")

class UserGroupMember(Base):
    # vínculo usuário ↔ grupo de usuários.
    __tablename__ = "user_group_members"
    __table_args__ = (UniqueConstraint("user_id", "group_id", name="uq_user_group_member"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("user_groups.id", ondelete="CASCADE"), index=True, nullable=False)

    user: Mapped[User] = relationship(back_populates="group_memberships")
    group: Mapped[UserGroup] = relationship(back_populates="members")

# -----------------------------------------
# Permissão de RELATÓRIO por grupo de usuário
# Atenção: reports.id é String(64) no modelo atual -> manter compatível!
# -----------------------------------------
class GroupReportPermission(Base):
    # vínculo grupo de usuários ↔ relatório
    __tablename__ = "group_report_permissions"
    __table_args__ = (UniqueConstraint("group_id", "report_id", name="uq_group_report"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("user_groups.id", ondelete="CASCADE"), index=True, nullable=False)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), index=True, nullable=False)  # String(64)!

    group: Mapped[UserGroup] = relationship(back_populates="report_permissions")

# -----------------------------------------
# RBAC por AÇÕES (roles/permissions) – opcional mas recomendado
# -----------------------------------------
class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(200))

    permissions: Mapped[list["RolePermission"]] = relationship(back_populates="role", cascade="all, delete-orphan")

class Permission(Base):
    __tablename__ = "permissions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(200))

class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_perm"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)

    role: Mapped[Role] = relationship(back_populates="permissions")
    permission: Mapped[Permission] = relationship()

class UserRole(Base):
    __tablename__ = "users_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), index=True, nullable=False)

    user: Mapped[User] = relationship(back_populates="roles")



# -----------------------------------------
# Reset Senha
# -----------------------------------------
class PasswordReset(Base):
    __tablename__ = "password_resets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reset_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="password_resets")


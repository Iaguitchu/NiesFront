from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Integer, ForeignKey, UniqueConstraint, Enum as SAEnum
import enum

class Base(DeclarativeBase): ...
    
class Group(Base):
    __tablename__ = "groups"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500))

    parent: Mapped["Group"] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list["Group"]] = relationship(back_populates="parent", cascade="all, delete")
    reports: Mapped[list["Report"]] = relationship(back_populates="group", cascade="all, delete-orphan")

class Report(Base):
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    title_description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    workspace_id: Mapped[str | None] = mapped_column(String(64))
    report_id: Mapped[str | None] = mapped_column(String(64))
    powerbi_url: Mapped[str | None] = mapped_column(String(1000))
    
    access_levels: Mapped[list["ReportAccessLevel"]] = relationship(back_populates="report", cascade="all, delete-orphan")
    group: Mapped[Group] = relationship(back_populates="reports")

class AccessLevel(str, enum.Enum):
    gestao = "gestao"
    estrategico = "estrategico"
    operacional = "operacional"
    outros = "outros"

class ReportAccessLevel(Base):
    __tablename__ = "report_access_levels"
    __table_args__ = (UniqueConstraint("report_id", "level", name="uq_report_level"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), index=True, nullable=False)
    level: Mapped[AccessLevel] = mapped_column(SAEnum(AccessLevel), nullable=False)


    report: Mapped["Report"] = relationship(back_populates="access_levels")
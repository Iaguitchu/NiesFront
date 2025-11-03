from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from db import get_db
from models.models import Group
from models.models_rbac import User
from services.security import require_admin
from core.templates import templates
from schemas.schemas_rbac import ReportGroupCreate, ReportSubgroupCreate
import re
import unicodedata

router = APIRouter(prefix="/register", tags=["register"])

normalize = re.compile(r"[^a-z0-9]+")
def normalize_words(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")  # remove acentos/ç
    value = value.lower().strip()
    value = normalize.sub("-", value).strip("-")              # troca tudo que não é [a-z0-9] por "-"
    return value

@router.get("/report-registration-group", response_class=HTMLResponse, include_in_schema=False)
def report_registration_group(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    groups = (
        db.query(Group)
          .filter(Group.is_active.is_(True))
          .order_by(Group.name.asc())
          .all()
    )
    ctx = {"request": request, "user": user, "groups": groups}
    return templates.TemplateResponse("cadastro-paineis.html", ctx)


@router.post("/report-groups", status_code=status.HTTP_201_CREATED)
def create_report_group(
    payload: ReportGroupCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    s_id = normalize_words(payload.name)

    # checa duplicidade por id (slug) e por nome (case-insensitive)
    has_id = db.query(Group).filter(Group.id == s_id).first()
    if has_id:
        raise HTTPException(status_code=409, detail="Já existe um grupo com este ID (slug).")

    has_name = (
        db.query(Group)
          .filter(func.lower(Group.name) == func.lower(payload.name))
          .first()
    )
    if has_name:
        raise HTTPException(status_code=409, detail="Já existe um grupo com este nome.")

    grp = Group(
        id=s_id,
        name=payload.name.strip(),
        is_active=True,
        # is_public/description adicionar depois
        # description=payload.description,
        # is_public=payload.is_public,
    )
    db.add(grp)
    db.commit()
    db.refresh(grp)
    return {"message": "Grupo criado com sucesso!", "id": grp.id}

@router.post("/report-subgroups", status_code=status.HTTP_201_CREATED)
def create_report_subgroup(
    payload: ReportSubgroupCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    parent = db.query(Group).filter(Group.id == payload.parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Grupo pai não encontrado.")

    s_id = normalize_words(payload.name)

    has_id = db.query(Group).filter(Group.id == s_id).first()
    if has_id:
        raise HTTPException(status_code=409, detail="Já existe um subgrupo com este ID (slug).")

    has_name_same_parent = (
        db.query(Group)
        .filter(
            func.lower(Group.name) == func.lower(payload.name),
            Group.parent_id == payload.parent_id,
        )
        .first()
    )
    if has_name_same_parent:
        raise HTTPException(status_code=409, detail="Já existe um subgrupo com este nome nesse grupo pai.")

    sub = Group(
        id=s_id,
        name=payload.name.strip(),
        parent_id=payload.parent_id,
        is_active=True,
        # is_public/description adicionar depois
        # description=payload.description,
        # is_public=payload.is_public,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return {"message": "Subgrupo criado com sucesso!", "id": sub.id}
# routes_admin_groups.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db
from models.models import Report
from models.models_rbac import UserGroup, User
from services.security import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/user-groups")  # lista grupos (esquerda)
def list_user_groups(
    db: Session = Depends(get_db),
    _u: User = Depends(require_admin),
):
    rows = db.query(UserGroup).order_by(UserGroup.name.asc()).all()
    return [{"id": g.id, "name": g.name, "description": g.description} for g in rows]

@router.get("/reports")  # lista painéis (direita)
def list_reports(
    db: Session = Depends(get_db),
    _u: User = Depends(require_admin),
):
    rows = (
        db.query(Report)
          .filter(Report.is_active == True)
          .order_by(Report.is_public.desc(), Report.name.asc())
          .all()
    )
    return {
        "public":  [{"id": r.id, "name": r.name} for r in rows if r.is_public],
        "private": [{"id": r.id, "name": r.name} for r in rows if not r.is_public],
    }
    

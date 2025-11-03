# routes_admin_groups.py
from fastapi import APIRouter, Depends, HTTPException, status   
from sqlalchemy.orm import Session
from db import get_db
from models.models import Report
from models.models_rbac import UserGroup, User
from services.security import require_admin
from typing import List
import uuid
from models.models_rbac import GroupReportPermission
from schemas.schemas_rbac import UserGroupCreate, UserGroupOut, ReportIdsIn

router = APIRouter()

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
    
@router.get("/user-groups/{group_id}/report-ids")
def get_group_report_ids(
    group_id: str,
    db: Session = Depends(get_db),
    _u: User = Depends(require_admin),
):
    ok = db.query(UserGroup).filter(UserGroup.id == group_id).first()
    if not ok:
        raise HTTPException(status_code=404, detail="Grupo de usuário não encontrado.")
    rows = (
        db.query(GroupReportPermission.report_id)
          .filter(GroupReportPermission.group_id == group_id)
          .all()
    )
    return [r[0] for r in rows]  # lista de IDs

@router.put("/user-groups/{group_id}/report-ids", status_code=status.HTTP_204_NO_CONTENT)
def set_group_report_ids(
    group_id: str,
    payload: ReportIdsIn,
    db: Session = Depends(get_db),
    _u: User = Depends(require_admin),
):
    grp = db.query(UserGroup).filter(UserGroup.id == group_id).first()
    if not grp:
        raise HTTPException(status_code=404, detail="Grupo de usuário não encontrado.")

    # valida IDs de reports
    if payload.report_ids:
        found = {r.id for r in db.query(Report.id).filter(Report.id.in_(payload.report_ids)).all()}
        missing = set(payload.report_ids) - found
        if missing:
            raise HTTPException(status_code=400, detail=f"Reports inexistentes: {', '.join(sorted(missing))}")

    # apaga permissões atuais e recria (idempotente + simples)
    db.query(GroupReportPermission).filter(GroupReportPermission.group_id == group_id).delete()
    for rep_id in payload.report_ids:
        db.add(GroupReportPermission(id=str(uuid.uuid4()), group_id=group_id, report_id=rep_id))
    db.commit()
    return

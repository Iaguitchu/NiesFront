# routers/index.py (ou outro router “páginas”)
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

from db import get_db
from core.templates import templates
from models.models import Report
from models.models_rbac import User, UserGroupMember, GroupReportPermission
from services.security import get_current_user_optional
from core.deps import with_menu

router = APIRouter(dependencies=[Depends(with_menu)])

@router.get("/report/{report_id}", response_class=HTMLResponse)
def report_view(
    request: Request,
    report_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    # Base: precisa estar ativo e existir
    q = db.query(Report).filter(
        Report.id == report_id,
        Report.is_active == True,
    )

    # Admin vê tudo
    if user and getattr(user, "is_admin", False):
        rep = q.first()
        if not rep:
            raise HTTPException(404, "Report not found")
    # Usuário comum: público OU permitido pelos grupos dele
    elif user:
        allowed_subq = (
            db.query(GroupReportPermission.report_id)
              .join(UserGroupMember, UserGroupMember.group_id == GroupReportPermission.group_id)
              .filter(UserGroupMember.user_id == user.id)
        )
        rep = (
            q.filter(or_(Report.is_public == True, Report.id.in_(allowed_subq)))
             .first()
        )
        if not rep:
            raise HTTPException(403, "You don't have permission to view this report")
    # Anônimo: só públicos
    else:
        rep = q.filter(Report.is_public == True).first()
        if not rep:
            raise HTTPException(403, "You don't have permission to view this report")

    ctx = {"request": request, "user": user, "report": rep}
    return templates.TemplateResponse("graficos.html", ctx)

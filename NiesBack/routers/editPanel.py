from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from db import get_db
from models.models import Group, Report
from models.models_rbac import User
from services.security import require_admin
from core.templates import templates
from core.deps import with_menu



router = APIRouter(dependencies=[Depends(with_menu)])

@router.get("/edit-report/{report_id}", response_class=HTMLResponse, include_in_schema=False)
def edit_report_page(
    report_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    # busca o report
    report = (
        db.query(Report)
          .filter(Report.id == report_id, Report.is_active.is_(True))
          .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Painel não encontrado.")

    # busca todos os grupos para o select
    groups = (
        db.query(Group)
          .filter(Group.is_active.is_(True))
          .order_by(Group.name.asc())
          .all()
    )

    # níveis de acesso atuais do report, ex.: {"gestao", "operacional"}
    current_levels = {ra.level.value for ra in report.access_levels}

    ctx = {
        "request": request,
        "user": user,
        "groups": groups,
        "report": report,
        "current_levels": current_levels,
    }
    return templates.TemplateResponse("editar-painel.html", ctx)



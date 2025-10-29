
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from db import get_db
from models.models_rbac import User, UserGroupMember, GroupReportPermission
from models.models import Report
from services.security import get_current_user_optional

from core.templates import templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def home(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    # base: só ativos
    q = db.query(Report).filter(Report.is_active == True)

    # permissões:
    if user and getattr(user, "is_admin", False):
        rows = q.order_by(Report.sort_order.is_(None),
                          Report.sort_order.asc(),
                          Report.name.asc()).all()
    elif user:
        allowed_subq = (
            db.query(GroupReportPermission.report_id)
              .join(UserGroupMember, UserGroupMember.group_id == GroupReportPermission.group_id)
              .filter(UserGroupMember.user_id == user.id)
        )
        rows = (q.filter(or_(Report.is_public == True, Report.id.in_(allowed_subq)))
                  .order_by(Report.sort_order.is_(None),
                            Report.sort_order.asc(),
                            Report.name.asc())
                  .all())
    else:
        rows = (q.filter(Report.is_public == True)
                  .order_by(Report.sort_order.is_(None),
                            Report.sort_order.asc(),
                            Report.name.asc())
                  .all())

    ctx = {"request": request, "user": user, "reports": rows}
    tpl = "index.html"
    return templates.TemplateResponse(tpl, ctx)

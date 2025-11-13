from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from db import get_db
from models.models import Report
from models.models_rbac import User, UserGroupMember, GroupReportPermission
from services.security import get_current_user_optional
from core.templates import templates
from core.deps import with_menu


router = APIRouter(dependencies=[Depends(with_menu)])

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def home(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    # ----------------- REPORTS -----------------
    q = db.query(Report).filter(Report.is_active.is_(True))
    pending_count = 0

    if user and getattr(user, "is_admin", False):
        rows = q.order_by(
            Report.sort_order.is_(None),
            Report.sort_order.asc(),
            Report.name.asc()
        ).all()
        pending_count = db.query(func.count(User.id))\
                          .filter(User.status == "pending")\
                          .scalar()
    elif user:
        allowed_subq = (
            db.query(GroupReportPermission.report_id)
              .join(UserGroupMember, UserGroupMember.group_id == GroupReportPermission.group_id)
              .filter(UserGroupMember.user_id == user.id)
        )
        rows = (q.filter(or_(Report.is_public.is_(True), Report.id.in_(allowed_subq)))
                  .order_by(Report.sort_order.is_(None),
                            Report.sort_order.asc(),
                            Report.name.asc())
                  .all())
    else:
        rows = (q.filter(Report.is_public.is_(True))
                  .order_by(Report.sort_order.is_(None),
                            Report.sort_order.asc(),
                            Report.name.asc())
                  .all())

    # envia o menu pro base.html
    ctx = {
        "request": request,
        "user": user,
        "reports": rows,
        "pending_users_count": pending_count
    }
    return templates.TemplateResponse("index.html", ctx)

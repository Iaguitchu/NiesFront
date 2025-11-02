
from fastapi import APIRouter, Depends, Request,HTTPException
from starlette import status
from fastapi.responses import HTMLResponse
from models.models_rbac import User
from services.security import require_admin
from core.templates import templates
from sqlalchemy.orm import Session
from db import get_db
from models.models_rbac import User, UserGroup
from models.models import Report


router = APIRouter()

@router.get("/user-registration-group", response_class=HTMLResponse, include_in_schema=False)
def user_registration_group(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    groups = (
        db.query(UserGroup)
          .order_by(UserGroup.name.asc())
          .all()
    )

    reports_private = (
        db.query(Report)
          .filter(
              Report.is_active == True,
              (Report.is_public == False) | (Report.is_public.is_(None))  # trata NULL como privado
          )
          .order_by(Report.sort_order.is_(None),
                    Report.sort_order.asc(),
                    Report.name.asc())
          .all()
    )

    ctx = {
        "request": request,
        "user": user,
        "groups": groups,
        "reports_private": reports_private,
    }
    return templates.TemplateResponse("cadastro-grupos.html", ctx)


from fastapi import APIRouter, Depends, Request,HTTPException
from starlette import status
from fastapi.responses import HTMLResponse
from models.models_rbac import User
from services.security import require_admin
from core.templates import templates
from sqlalchemy.orm import Session
from db import get_db
from models.models_rbac import User, UserGroup, GroupReportPermission
from models.models import Report
from schemas.schemas_rbac import UserGroupCreate, UserGroupOut
from sqlalchemy import func, distinct
from core.deps import with_menu


router = APIRouter(prefix="/register", tags=["register"], dependencies=[Depends(with_menu)])

@router.get("/user-register", response_class=HTMLResponse, include_in_schema=False)
def user_registration(request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    
    user_groups = db.query(UserGroup).order_by(UserGroup.name.asc()).all()
    ctx= { "request": request,
            "user": user,
            "user_groups":user_groups
          }

    return templates.TemplateResponse("cadastro-usuarios.html", ctx)

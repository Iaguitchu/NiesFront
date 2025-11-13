from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form
from sqlalchemy.orm import Session
from db import get_db
from models.models_rbac import User, UserStatus
from schemas.schemas_rbac import UserCreate, LoginIn, TokenOut, UserOut
from services.security import *
from datetime import timedelta, date
from fastapi.responses import HTMLResponse
from core.templates import templates
from starlette import status as http_status
from services.password_reset import get_valid_password_reset, mark_used, hash_password
from core.deps import with_menu


router = APIRouter(prefix="/details", tags=["details"], dependencies=[Depends(with_menu)])


@router.get('/panel-detail')
def panel(request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    ctx= { "request": request,
            "user": user}

    return templates.TemplateResponse("detalhes-painel.html", ctx)
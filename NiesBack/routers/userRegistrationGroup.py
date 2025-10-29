
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

@router.get("/user-registration-group", response_class=HTMLResponse, include_in_schema=False)
def userRegistrationGroup(request: Request):
    tpl = "Base-Cadastro-Usuarios.html"
    ctx = {"request": request}
    return templates.TemplateResponse(tpl, ctx)
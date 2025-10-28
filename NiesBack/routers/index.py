
from typing import Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from services.security import get_current_user_optional
from models.models_rbac import User
from core.templates import templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request, user: Optional[User] = Depends(get_current_user_optional)):
    ctx = {"request": request, "user": user}
    # logado → index_logada.html; anônimo → index.html
    tpl = "index_logada.html" if user else "index.html"
    return templates.TemplateResponse(tpl, ctx)

from fastapi import APIRouter, Depends, Request,HTTPException
from starlette import status
from fastapi.responses import HTMLResponse

from models.models_rbac import User
from services.security import get_current_user_optional


from core.templates import templates

router = APIRouter()

def require_admin(
    user: User | None = Depends(get_current_user_optional)) -> User:
    if not user:
        # 303 + Location faz o redirect
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/auth/login"},
        )
    if not getattr(user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/"},
        )
    return user

@router.get("/user-registration-group", response_class=HTMLResponse, include_in_schema=False)
def user_registration_group(request: Request, user: User = Depends(require_admin)):
    return templates.TemplateResponse("Base-Cadastro-Usuarios.html", {"request": request, "user": user})

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

# from services.reset_password import send_reset_code

router = APIRouter(prefix="/auth", tags=["auth"])

ACCESS_EXPIRES = timedelta(minutes=1)
REFRESH_EXPIRES = timedelta(days=7)

def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("cadastro.html", {"request": request})

@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    email = _normalize_email(user_in.email)
    if db.query(User).filter(User.email == email).first():
        teste = db.query(User).filter(User.email == email).first()
        print(teste)
        raise HTTPException(400, "Email already registered")
    if db.query(User).filter(User.cpf == user_in.cpf).first():
        raise HTTPException(400, "CPF already registered")

    u = User(
        name=user_in.name.strip(),
        cpf=user_in.cpf.strip(),
        email=email,
        phone=(user_in.phone or "").strip(),
        valid_from=user_in.valid_from,
        valid_to=user_in.valid_to,
        password_hash=hash_password(user_in.password),
        status=UserStatus.pending,  # ficará pendente até aprovação
        is_admin=False,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, response: Response, db: Session = Depends(get_db)):
    invalid_err = HTTPException(401, "E-mail ou senha inválidos.")
    u = db.query(User).filter(User.email == _normalize_email(data.email)).first()
    if u:
    # Se não tem senha definida ainda (ex.: acabou de confirmar convite)
        if u.password_hash == "" :
            raise HTTPException(status_code=403, detail="Defina sua senha pelo link enviado por e-mail.")

    if not u or not verify_password(data.password, u.password_hash):
        raise invalid_err

    today = date.today()

    # 1) Se tem data final e já passou, bloqueia
    if u.valid_to and today > u.valid_to:
        raise HTTPException(status_code=403, detail=f"Seu período de acesso expirou em {u.valid_to.strftime('%d/%m/%Y')}.")

    # 2) Se não está aprovado, avalia janela: se já pode, aprova; senão bloqueia
    if u.status != UserStatus.approved:
        inside_window = (
            (u.valid_from is None or today >= u.valid_from) and
            (u.valid_to   is None or today <= u.valid_to)
        )
        if inside_window:
            u.status = UserStatus.approved
            db.add(u)
            db.commit()
            db.refresh(u)
        else:
            if u.valid_from and today < u.valid_from:
                # ainda não chegou a data de início
                raise HTTPException(status_code=403, detail=f"Seu acesso estará liberado a partir de {u.valid_from.strftime('%d/%m/%Y')}.")
            # fora da janela por outro motivo (ou pendente sem janela)
            raise HTTPException(status_code=403, detail="Usuário não aprovado.")

    # 3) Tudo ok → emite tokens e cookies
    access = create_access_token(sub=str(u.id), is_admin=u.is_admin, expires_delta=ACCESS_EXPIRES)
    refresh = create_refresh_token(sub=str(u.id), expires_delta=REFRESH_EXPIRES)

    response.set_cookie(
        key="access_token",
        value=access,
        httponly=True,
        secure=False,   # Produção + HTTPS => True
        samesite="lax",
        path="/",
        max_age=int(ACCESS_EXPIRES.total_seconds()),
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=int(REFRESH_EXPIRES.total_seconds()),
    )
    return TokenOut(access_token=access, refresh_token=refresh)



@router.post("/refresh", response_model=TokenOut)
def refresh_token(
    request: Request,
    response: Response,
    payload: Optional[TokenOut] = None,                      # permite body opcional
    db: Annotated[Session, Depends(get_db)] = None,
):
    """
    Emite um novo access_token (e rotaciona o refresh_token, opcionalmente).
    Lê o refresh_token do body (payload.refresh_token) **ou** do cookie HttpOnly.
    Também atualiza os cookies.
    """
    # 1) Obter refresh_token do body ou do cookie
    rt = (payload.refresh_token if payload else None) or request.cookies.get("refresh_token")
    if not rt:
        raise HTTPException(400, "Missing refresh_token")

    # 2) Validar e checar revogação
    claims = decode_token_safely(rt, verify_type="refresh")
    if not claims:
        raise HTTPException(401, "Invalid refresh token")

    sub = claims.get("sub")
    if not sub:
        raise HTTPException(401, "Invalid refresh token")

    # 3) Carregar usuário
    # (use db.get em vez de query().get)
    u = db.get(User, int(sub))
    if not u or u.status != UserStatus.approved:
        raise HTTPException(403, "User not allowed")

    # 4) Emitir novo access
    new_access = create_access_token(
        sub=str(u.id),
        is_admin=u.is_admin,
        expires_delta=ACCESS_EXPIRES,
    )

    # 5) (Opcional, recomendado) Rotacionar o refresh

    new_refresh, = create_refresh_token(
        sub=str(u.id),
        expires_delta=REFRESH_EXPIRES,
    )

    # 6) Atualizar cookies
    response.set_cookie(
        key="access_token",
        value=new_access,
        httponly=True,
        secure=False,      # True em produção com HTTPS
        samesite="lax",    # "none" se front for outra origem/porta (com HTTPS)
        path="/",
        max_age=int(ACCESS_EXPIRES.total_seconds()),
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=int(REFRESH_EXPIRES.total_seconds()),
    )

    # 7) Retornar também no body (útil se o front usa Bearer em chamadas XHR)
    return TokenOut(access_token=new_access, refresh_token=new_refresh)



@router.post("/logout")
def logout(response: Response):
    

    # apaga cookies
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"ok": True}

# @router.post("/reset-password/")
# def reset_password(data: ResetPasswordIn, db: Session = Depends(get_db)):
#    return send_reset_code(_normalize_email(data.email), db)
@router.get("/set-password", response_class=HTMLResponse)
def set_password_form(request: Request, rid: str, token: str, db: Session = Depends(get_db)):
    pr = get_valid_password_reset(db, rid, token)
    if not pr:
        raise HTTPException(status_code=400, detail="Link inválido ou expirado.")
    return templates.TemplateResponse(
        "set_password.html",
        {"request": request, "rid": rid, "token": token},
        status_code=200
    )

@router.post("/set-password")
def set_password_submit(
    request: Request,
    rid: str = Form(...),
    token: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    pr = get_valid_password_reset(db, rid, token)
    if not pr:
        raise HTTPException(status_code=400, detail="Link inválido ou expirado.")

    # Validações de força/igualdade
    if password != password_confirm:
        raise HTTPException(status_code=400, detail="As senhas não coincidem.")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 8 caracteres.")
    # (Opcional) impor números/letras/maiúsculas/especiais

    user = db.get(User, pr.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    user.password_hash = hash_password(password)
    db.add(user)
    db.commit()

    mark_used(db, pr)

    # Redireciona para login
    return templates.TemplateResponse(
        "mensagem.html",
        {"request": request, "title": "Senha definida", "message": "Senha definida com sucesso. Você já pode fazer login."},
        status_code=http_status.HTTP_200_OK
    )

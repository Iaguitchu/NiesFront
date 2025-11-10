
from fastapi import APIRouter, Depends, Request,HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from models.models_rbac import User
from services.security import require_admin
from core.templates import templates
from sqlalchemy.orm import Session
from db import get_db
from models.models_rbac import User, UserGroup, UserGroupMember, UserStatus
from datetime import date
from typing import List, Optional
from core.deps import with_menu
from core.settings import settings
from core.tokens import make_invite_token, read_invite_token
from core.email import send_email
from sqlalchemy import select, or_
from starlette import status as http_status
from services.password_reset import create_password_reset
from schemas.schemas_rbac import UserCreate

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

@router.post("/user-register", name="post_user_registration")
async def post_user_registration(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    # user: User = Depends(require_admin)  # se quiser exigir admin
):
    # 1) checagem duplicidade
    existing = (
        db.query(User)
          .filter(or_(User.email == user_in.email, User.cpf == user_in.cpf))
          .first()
    )
    if existing:
        if existing.email == user_in.email:
            raise HTTPException(status_code=400, detail="E-mail já foi cadastrado.")
        raise HTTPException(status_code=400, detail="CPF já foi cadastrado.")

    # 2) monta payload do convite (datas já são date -> serialize para iso)
    payload = {
        "name": user_in.name.strip(),
        "cpf": user_in.cpf.strip(),
        "email": user_in.email.strip().lower(),
        "phone": (user_in.phone or "").strip() or None,
        "status": user_in.status,  # "approved" | "pending"
        "valid_from": user_in.valid_from.isoformat() if user_in.valid_from else None, #isoformat transforma data em (YYYY-MM-DD)
        "valid_to": user_in.valid_to.isoformat() if user_in.valid_to else None,
        "group_ids": user_in.group_ids or [],
    }
    token = make_invite_token(payload)

    confirm_url = f"{settings.PUBLIC_BASE_URL}/register/confirm?token={token}"

    subject = "Confirmação de acesso"
    text = (
        f"Olá, {user_in.name},\n\n"
        "Um administrador criou um acesso para você.\n"
        "Clique no link abaixo para confirmar e ativar seu usuário:\n\n"
        f"{confirm_url}\n\n"
        "Se você não solicitou, ignore este e-mail."
    )
    html = f"""
    <p>Olá, <strong>{user_in.name}</strong>,</p>
    <p>Um administrador criou um acesso para você.</p>
    <p>Clique para confirmar e ativar seu usuário:</p>
    <p><a href="{confirm_url}">Confirmar meu acesso</a></p>
    <p>Se você não solicitou, ignore este e-mail.</p>
    """

    send_email(to=user_in.email, subject=subject, body_text=text, body_html=html)

    return JSONResponse(
    {
        "ok": True,
        "message": f"Convite enviado para {user_in.email}.\nVerifique a caixa de SPAM"
    },
    status_code=200,
)


@router.get("/confirm", response_class=HTMLResponse)
def confirm_invite(request: Request, token: str, db: Session = Depends(get_db)):
    # Valida token
    try:
        data = read_invite_token(token, max_age_seconds=settings.INVITE_EXPIRES_SECONDS)
    except Exception:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")

    # Extrai payload
    name = data["name"]
    cpf = data["cpf"]
    email = data["email"]
    phone = data.get("phone")
    status_str = data.get("status", "pending")
    vfrom = date.fromisoformat(data["valid_from"]) if data.get("valid_from") else None
    vto = date.fromisoformat(data["valid_to"]) if data.get("valid_to") else None
    group_ids = data.get("group_ids", [])

    # Já existe usuário?
    existing: User | None = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()

    if existing:
        # Atualiza campos e status, se fizer sentido
        existing.name = name
        existing.cpf = cpf
        existing.phone = phone
        existing.valid_from = vfrom
        existing.valid_to = vto
        # Se já estava pending, ativa conforme 'status' do convite
        if existing.status == UserStatus.pending and status_str == "approved":
            existing.status = UserStatus.approved
        db.add(existing)
        user_obj = existing
    else:
        # Cria o usuário: status conforme convite
        user_obj = User(
            name=name,
            cpf=cpf,
            email=email,
            phone=phone,
            valid_from=vfrom,
            valid_to=vto,
            status=UserStatus.approved if status_str == "approved" else UserStatus.pending,
            is_admin=False,
            password_hash="",  #forçar setar a senha no primeiro acesso.
        )
        db.add(user_obj)
        db.flush()  # para ter user_obj.id

    # Sincroniza grupos
    if group_ids:
        # limpa memberships atuais e adiciona os do convite
        db.query(UserGroupMember).filter(UserGroupMember.user_id == user_obj.id).delete()
        # valida IDs existentes
        groups = db.execute(select(UserGroup).where(UserGroup.id.in_(group_ids))).scalars().all()
        for g in groups:
            db.add(UserGroupMember(user_id=user_obj.id, group_id=g.id))

    db.commit()

    reset_id, raw = create_password_reset(db, user_obj)
    setpwd_url = f"{settings.PUBLIC_BASE_URL}/auth/set-password?rid={reset_id}&token={raw}"

    # Redireciona para página de sucesso / login
    return templates.TemplateResponse(
    "mensagem.html",
    {
        "request": request,
        "title": "Usuário confirmado",
        "message": f"Seu usuário foi confirmado. Agora defina sua senha: <a href='{setpwd_url}'>Definir senha</a>",
    },
    status_code=200,
)
# core/deps.py (ou onde você guarda os deps globais)
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from db import get_db
from core.menu import build_menu_for_user
from services.security import get_current_user_optional
from models.models_rbac import User

def with_menu(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    """
    Injeta em request.state.menu apenas os grupos/subgrupos
    com pelo menos 1 relatório permitido ao usuário (ou ancestrais).
    Admin vê tudo.
    """
    request.state.menu = build_menu_for_user(db, user)
    return None  # side-effect only

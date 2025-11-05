from fastapi import Depends, Request
from db import get_db
from core.menu import build_menu

def with_menu(request: Request, db=Depends(get_db)):
    request.state.menu = build_menu(db)
    return None  # nada a retornar; só side-effect

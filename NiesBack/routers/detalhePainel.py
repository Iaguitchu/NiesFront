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

router = APIRouter(prefix="/details", tags=["details"])
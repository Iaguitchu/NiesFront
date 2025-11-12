from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Dict, Any, List
import httpx # usada para fazer requisições HTTP assíncronas

from models.models_rbac import User 
from typing import Optional
from models.models import Group, Report
from db import get_db
from core.settings import settings, AUTH_URL
from schemas.schemas import GroupOut, GroupTreeOut, ReportOut
from services.security import require_admin

from models.models_rbac import UserGroupMember, GroupReportPermission
from services.security import get_current_user_optional

router = APIRouter(prefix="/api/powerbi", tags=["powerbi"])

async def get_app_token() -> str:
    data = {
        "grant_type": "client_credentials",
        "client_id": settings.AZURE_CLIENT_ID,
        "client_secret": settings.AZURE_CLIENT_SECRET,
        "scope": settings.PBI_SCOPE,
    }
    async with httpx.AsyncClient(timeout=20) as client:                 #timout evita request pendurados
        r = await client.post(AUTH_URL, data=data)                      #chama o endpoint do Azure AD (token).
        if r.status_code != 200:
            raise HTTPException(r.status_code, f"Auth error: {r.text}")
        return r.json()["access_token"]                                 #retorna access_token do JSON (string JWT de app).

@router.get("/embed-info")
async def embed_info(
    reportId: str = Query(...),
    username: Optional[str] = Query(None, description="Usuário final para aplicar RLS"),
    roles: Optional[str] = Query(None, description="Roles separadas por vírgula"),
    db: Session = Depends(get_db),
):
    rep = (
        db.query(Report)
          .filter(Report.id == reportId, Report.is_active == True)
          .first()
    )
    if not rep:
        raise HTTPException(404, "Report not found")

    app_token = await get_app_token()
    headers = {"Authorization": f"Bearer {app_token}"}

    # 1) info do report
    report_url = f"{settings.PBI_API}/groups/{rep.workspace_id}/reports/{rep.report_id}"
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(report_url, headers=headers)
        if r.status_code != 200:
            raise HTTPException(r.status_code, f"Get report error: {r.text}")
        report = r.json()
        embed_url = report["embedUrl"]
        dataset_id = report["datasetId"]

        # 2) corpo do GenerateToken
        body = {"accessLevel": "View"}
        if username:
            roles_list = []
            for r in (roles or "").split(","): #separa por virgula
                if r.strip(): #tira espaços em branco
                    roles_list.append(r.strip())
            body["identities"] = [{
                "username": username,
                "roles": roles_list,
                "datasets": [dataset_id]
            }]

        # 3) embed token
        gen_token_url = f"{settings.PBI_API}/groups/{rep.workspace_id}/reports/{rep.report_id}/GenerateToken"
        r2 = await client.post(gen_token_url, headers=headers, json=body)
        if r2.status_code != 200:
            raise HTTPException(r2.status_code, f"Generate token error: {r2.text}")
        embed_token = r2.json()["token"]

    return {
        "groupId": rep.workspace_id,
        "reportId": rep.report_id,
        "datasetId": dataset_id,
        "embedUrl": embed_url,
        "accessToken": embed_token,
    }


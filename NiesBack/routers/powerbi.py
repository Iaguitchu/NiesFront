from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
import httpx # usada para fazer requisições HTTP assíncronas

from models import Group
from db import get_db
from core.settings import settings, AUTH_URL

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

@router.get("/groups")
def list_groups(db: Session = Depends(get_db)):
    rows = db.query(Group).filter(Group.is_active == True).all()
    for g in rows:
        return [{"id": g.id, "name": g.name}]

@router.get("/embed-info")
async def embed_info(groupId: str = Query(..., alias="groupId"),
                     db: Session = Depends(get_db)):
    g: Group | None = db.query(Group).filter(Group.id == groupId, Group.is_active == True).first() #pega o grupo do banco ou None
    if not g:
        raise HTTPException(404, "Group not found")

    token = await get_app_token()

    # 1) Buscar informações do report (embedUrl + datasetId)
    report_url = f"{settings.PBI_API}/groups/{g.workspace_id}/reports/{g.report_id}"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(report_url, headers=headers)
        if r.status_code != 200:
            raise HTTPException(r.status_code, f"Get report error: {r.text}")
        report = r.json()
        embed_url = report["embedUrl"]
        dataset_id = report["datasetId"]

        # 2) Gerar Embed Token (View)
        gen_token_url = f"{settings.PBI_API}/groups/{g.workspace_id}/reports/{g.report_id}/GenerateToken"
        body: Dict[str, Any] = {"accessLevel": "View"}
        r2 = await client.post(gen_token_url, headers=headers, json=body)
        if r2.status_code != 200:
            raise HTTPException(r2.status_code, f"Generate token error: {r2.text}")
        embed_token = r2.json()["token"]

    return {
        "groupId": g.workspace_id,
        "reportId": g.report_id,
        "datasetId": dataset_id,
        "embedUrl": embed_url,
        "accessToken": embed_token,
    }

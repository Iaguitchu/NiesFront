from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
import httpx # usada para fazer requisições HTTP assíncronas

from models import Group, Report
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
    lista = []
    for g in rows:
        lista.append({"id": g.id, "name": g.name})
    return lista
    

@router.get("/reports")
def list_reports(groupId: str = Query(...), db: Session = Depends(get_db)):
    grp = db.query(Group).filter(Group.id == groupId, Group.is_active == True).first()
    if not grp:
        raise HTTPException(404, "Group not found")
    rows = (
        db.query(Report)
          .filter(Report.group_id == groupId, Report.is_active == True)
          .order_by(Report.sort_order.nulls_last(), Report.name.asc())
          .all()
    )
    return [
        {
            "id": r.id,
            "name": r.name,
            "group_id": r.group_id,
        } for r in rows
    ]


@router.get("/embed-info")
async def embed_info(
    reportId: str = Query(...),  # ex.: 'selvagens'
    db: Session = Depends(get_db)
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

        # 2) embed token
        gen_token_url = f"{settings.PBI_API}/groups/{rep.workspace_id}/reports/{rep.report_id}/GenerateToken"
        r2 = await client.post(gen_token_url, headers=headers, json={"accessLevel": "View"})
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


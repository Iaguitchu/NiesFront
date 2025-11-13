from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
import httpx # usada para fazer requisições HTTP assíncronas
from typing import Optional
from models.models import Report
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




@router.get("/embed-info")
async def embed_info(
    reportId: str = Query(...),
    username: Optional[str] = None,
    roles: Optional[str] = None,
    db: Session = Depends(get_db),
):
    rep = (
        db.query(Report)
          .filter(Report.id == reportId, Report.is_active == True)
          .first()
    )

    if not rep:
        raise HTTPException(404, "Report not found")

    # -------------------------
    # CASO 1 — É externo
    # -------------------------
    if rep.powerbi_url and not rep.workspace_id:
        return {
            "externalUrl": rep.powerbi_url
        }

    # -------------------------
    # CASO 2 — Interno (com token)
    # -------------------------
    app_token = await get_app_token()
    headers = {"Authorization": f"Bearer {app_token}"}

    report_url = f"{settings.PBI_API}/groups/{rep.workspace_id}/reports/{rep.report_id}"

    async with httpx.AsyncClient(timeout=20) as client:
        # GET report info
        r = await client.get(report_url, headers=headers)
        if r.status_code != 200:
            raise HTTPException(r.status_code, r.text)
        report = r.json()

        embed_url = report["embedUrl"]
        dataset_id = report["datasetId"]

        # Generate token
        body = {"accessLevel": "View"}

        if username:
            roles_list = [x.strip() for x in (roles or "").split(",") if x.strip()]
            body["identities"] = [{
                "username": username,
                "roles": roles_list,
                "datasets": [dataset_id]
            }]

        gen_url = f"{settings.PBI_API}/groups/{rep.workspace_id}/reports/{rep.report_id}/GenerateToken"
        r2 = await client.post(gen_url, headers=headers, json=body)

        if r2.status_code != 200:
            raise HTTPException(r2.status_code, r2.text)

        token = r2.json()["token"]

    return {
        "groupId": rep.workspace_id,
        "reportId": rep.report_id,
        "datasetId": dataset_id,
        "embedUrl": embed_url,
        "accessToken": token
    }



 



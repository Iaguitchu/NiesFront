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

def _build_tree(groups: List[Group]) -> List[Group]:
    by_parent: dict[str | None, list[Group]] = {}       #Cria o dicionário vazio “pai → filhos”, chave é str ou None e o valor é uma lista de Group
    for g in groups:
        by_parent.setdefault(g.parent_id, []).append(g) #Adiciona no dicionario id com parent id e value uma lista de Group exemplo: { None: [Group("animais")], "animais": [Group("domesticos"), Group("selvagens")] }
    def attach(node: Group):
        node.children = by_parent.get(node.id, [])
        for c in node.children:
            attach(c)                                   #chama a função de novo para cada filho, para também preencher os netos, bisnetos, etc.
    roots = by_parent.get(None, [])                     
    for r in roots:
        attach(r)                                       
    return roots

def _descendants_ids(db: Session, root_id: str) -> set[str]:
    # busca tudo e faz DFS em memória
    groups = db.query(Group).filter(Group.is_active == True).all()
    children_by_parent = {}
    for g in groups:
        children_by_parent.setdefault(g.parent_id, []).append(g.id) #Adiciona no dicionario id com parent id e value uma lista de Group exemplo: { None: [Group("animais")], "animais": [Group("domesticos"), Group("selvagens")] }
    result = set([root_id])
    stack = [root_id]
    while stack:
        cur = stack.pop()
        for child_id in children_by_parent.get(cur, []):
            if child_id not in result:
                result.add(child_id)
                stack.append(child_id)
    return result

@router.get("/groups", response_model=list[GroupOut] | list[GroupTreeOut])
def list_groups(
    tree: bool = Query(False, description="Se true, retorna a árvore de grupos"),
    db: Session = Depends(get_db),
):
    rows = db.query(Group).filter(Group.is_active == True).all()
    if not tree:
        tops = []
        for g in rows:
            if g.parent_id is None:
                tops.append(g)
        return tops
    #árvore completa
    return _build_tree(rows)

@router.get("/groups/{group_id}/children", response_model=list[GroupOut])
def list_children(group_id: str, db: Session = Depends(get_db)):
    rows = db.query(Group).filter(
        Group.is_active == True,
        Group.parent_id == group_id
    ).all()
    return rows

@router.get("/reports", response_model=list[ReportOut])
def list_reports_by_group(
    groupId: str = Query(..., description="slug (ou name) do grupo raiz"),
    db: Session = Depends(get_db),
    current: Optional[User] = Depends(get_current_user_optional),
):
    # 1) Resolva o grupo raiz 
    g = db.query(Group).filter(Group.is_active == True, Group.name == groupId).first()
    if not g:
        return []

    # 2) Todos os descendentes + o próprio
    group_ids = _descendants_ids(db, g.id)

    # 3) Base query: relatórios ativos dos grupos (raiz + filhos)
    q = db.query(Report).filter(
        Report.is_active == True,
        Report.group_id.in_(group_ids),
    )

    # 4) Permissões
    if current and getattr(current, "is_admin", False):
        rows = q.order_by(Report.sort_order.is_(None), Report.sort_order.asc(), Report.name.asc()).all()
    elif current:
        allowed_subq = (
            db.query(GroupReportPermission.report_id)
              .join(UserGroupMember, UserGroupMember.group_id == GroupReportPermission.group_id)
              .filter(UserGroupMember.user_id == current.id)
        )
        rows = (
            q.filter(or_(Report.is_public == True, Report.id.in_(allowed_subq)))
             .order_by(Report.sort_order.is_(None), Report.sort_order.asc(), Report.name.asc())
             .all()
        )
    else:
        rows = (
            q.filter(Report.is_public == True)
             .order_by(Report.sort_order.is_(None), Report.sort_order.asc(), Report.name.asc())
             .all()
        )

    # 5) Monta a saída no formato que seu front espera
    out = []
    for r in rows:
        out.append(ReportOut(
            id=r.id,
            name=r.name,
            thumbnail_url=r.thumbnail_url,
            title_description=r.title_description,
            description=r.description,
            image_url=r.image_url,
        ))
    return out

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


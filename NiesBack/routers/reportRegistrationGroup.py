from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from db import get_db
from models.models import Group, Report, ReportAccessLevel, AccessLevel
from models.models_rbac import User
from services.security import require_admin
from core.templates import templates
from schemas.schemas_rbac import ReportGroupCreate, ReportSubgroupCreate
from schemas.schemas import ReportOut, ReportAccessLevelEnum
import re
import unicodedata
from core.deps import with_menu
from routers.media_uploads import MEDIA_DIR, MEDIA_URL

router = APIRouter(prefix="/register", tags=["register"], dependencies=[Depends(with_menu)])

normalize = re.compile(r"[^a-z0-9]+")
def normalize_words(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")  # remove acentos/ç
    value = value.lower().strip()
    value = normalize.sub("-", value).strip("-")              # troca tudo que não é [a-z0-9] por "-"
    return value

@router.get("/report-registration-group", response_class=HTMLResponse, include_in_schema=False)
def report_registration_group(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    # pega todos os grupos (1 query)
    groups = (
        db.query(Group.id, Group.name, Group.parent_id)
          .filter(Group.is_active.is_(True))
          .order_by(Group.name.asc())
          .all()
    )
    gmap = {}
    for g in groups:
        gmap[g.id] = {"name": g.name, "parent_id": g.parent_id}

    def build_path(group_id: str) -> str:
        parts = []
        seen = set()
        gid = group_id
        # sobe até a raiz (protege contra ciclos)
        while gid and gid in gmap and gid not in seen:
            parts.append(gmap[gid]["name"])
            seen.add(gid)
            gid = gmap[gid]["parent_id"]
        return " >> ".join(reversed(parts)) if parts else "-"

    # pega reports ativos (1 query)
    reports = db.query(Report).filter(Report.is_active.is_(True)).all()

    # prepara linhas para o template
    report_rows = []
    for r in reports:
        row = {
            "r": r,
            "group_path": build_path(r.group_id)
        }
        report_rows.append(row)
        
    ctx = {
        "request": request,
        "user": user,
        "groups": groups,
        "report_rows": report_rows
    }

    return templates.TemplateResponse("cadastro-paineis.html", ctx)


@router.post("/report-groups", status_code=status.HTTP_201_CREATED)
def create_report_group(
    payload: ReportGroupCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    s_id = normalize_words(payload.name)

    # checa duplicidade por id (slug) e por nome (case-insensitive)
    has_id = db.query(Group).filter(Group.id == s_id).first()
    if has_id:
        raise HTTPException(status_code=409, detail="Já existe um grupo com este nome.")
    

    grp = Group(
        id=s_id,
        name=payload.name.strip(),
        is_active=True,
        description=payload.description,
    )
    db.add(grp)
    db.commit()
    db.refresh(grp)
    return {"message": "Grupo criado com sucesso!", "id": grp.id}

@router.post("/report-subgroups", status_code=status.HTTP_201_CREATED)
def create_report_subgroup(
    payload: ReportSubgroupCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    parent = db.query(Group).filter(Group.id == payload.parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Grupo pai não encontrado.")

    s_id = normalize_words(payload.name)

    has_id = db.query(Group).filter(Group.id == s_id).first()
    if has_id:
        raise HTTPException(status_code=409, detail="Já existe um subgrupo com este nome.")

    has_name_same_parent = (
        db.query(Group)
        .filter(
            func.lower(Group.name) == func.lower(payload.name),
            Group.parent_id == payload.parent_id,
        )
        .first()
    )
    if has_name_same_parent:
        raise HTTPException(status_code=409, detail="Já existe um subgrupo com este nome nesse grupo pai.")

    sub = Group(
        id=s_id,
        name=payload.name.strip(),
        parent_id=payload.parent_id,
        is_active=True,
        description=payload.description
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return {"message": "Subgrupo criado com sucesso!", "id": sub.id}


@router.post("/reports", response_model=ReportOut)
def create_report(payload: ReportOut, db: Session = Depends(get_db)):
    has_url = bool(payload.powerbi_url)
    has_ids = bool(payload.workspace_id and payload.report_id)

    # define o id (slug)
    if not payload.id:
        s_id = normalize_words(payload.name)
        exists = db.query(Report).filter(Report.id == s_id).first()
        if exists:
            raise HTTPException(status_code=409, detail="Já existe um powerbi com este Nome.")
    else:
        s_id = normalize_words(payload.id)

    # valida modo PowerBI (XOR)
    if not (has_url ^ has_ids):
        raise HTTPException(
            status_code=400,
            detail="Envie OU powerbi_url OU (workspace_id e report_id)."
        )

    # cria o Report
    report = Report(
        id=s_id,
        name=payload.name,
        group_id=payload.group_id,
        description=payload.description,
        image_url=payload.image_url,
        powerbi_url=payload.powerbi_url if has_url else None,
        workspace_id=payload.workspace_id if has_ids else None,
        report_id=payload.report_id if has_ids else None,
        is_public=payload.is_public,
    )
    db.add(report)
    db.flush()  # garante report.id disponível para as FKs

    # popula N níveis de acesso
    # payload.access_levels é uma lista de ReportAccessLevelEnum
    for lvl in payload.access_levels:
        # lvl pode ser Enum ou str;
        if isinstance(lvl, str):
            lvl_value = lvl
        else:
            lvl_value = lvl.value  # Enum -> str

        db.add(ReportAccessLevel(
            report_id=report.id,
            level=AccessLevel(lvl_value)  # converte para Enum do modelo
        ))

    db.commit()
    db.refresh(report)

    # monta saída com os níveis já persistidos
    out_levels = [
        ReportAccessLevelEnum(ra.level.value)  # model Enum -> schema Enum
        for ra in report.access_levels
    ]

    return ReportOut(
        id=report.id,
        name=report.name,
        title_description=report.title_description,
        description=report.description,
        image_url=report.image_url,
        powerbi_url=report.powerbi_url,
        workspace_id=report.workspace_id,
        report_id=report.report_id,
        group_id=report.group_id,
        is_public=report.is_public,
        access_levels=out_levels,
    )


@router.put("/reports/{report_id}", response_model=ReportOut)
def update_report(
    report_id: str,
    payload: ReportOut,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Painel não encontrado.")
    

    has_url = bool(payload.powerbi_url)
    has_ids = bool(payload.workspace_id and payload.report_id)

    # Se mandou URL e IDs juntos → erro
    if has_url and has_ids:
        raise HTTPException(
            status_code=400,
            detail="Não envie powerbi_url junto com workspace_id/report_id. Escolha apenas um modo."
        )

    # Se não mandou nem URL nem IDs → erro
    if not has_url and not has_ids:
        raise HTTPException(
            status_code=400,
            detail="Envie OU powerbi_url OU (workspace_id e report_id)."
    )

    old_image_url = report.image_url

    report.name = payload.name
    report.group_id = payload.group_id
    report.description = payload.description
    report.image_url = payload.image_url
    report.is_public = payload.is_public

    if has_url:
        report.powerbi_url = payload.powerbi_url
        report.workspace_id = None
        report.report_id = None
    else:
        report.workspace_id = payload.workspace_id
        report.report_id = payload.report_id
        report.powerbi_url = None

    # limpa níveis antigos
    db.query(ReportAccessLevel).filter(
        ReportAccessLevel.report_id == report.id
    ).delete()

    # recria níveis conforme o payload
    for lvl in payload.access_levels:
        if isinstance(lvl, str):
            lvl_value = lvl
        else:
            lvl_value = lvl.value

        db.add(ReportAccessLevel(
            report_id=report.id,
            level=AccessLevel(lvl_value),
        ))

    db.commit()
    db.refresh(report)

    out_levels = [
        ReportAccessLevelEnum(ra.level.value)
        for ra in report.access_levels
    ]

    if old_image_url and old_image_url != report.image_url:
        try:
            # old_image_url vem tipo "/media/abcd1234.jpg"
            prefix = MEDIA_URL.rstrip("/") + "/"
            if old_image_url.startswith(prefix):
                filename = old_image_url[len(prefix):]  # "abcd1234.jpg"
                old_path = MEDIA_DIR / filename
                if old_path.is_file():
                    old_path.unlink()
        except Exception as e:
            # aqui pode só logar, pra não quebrar a requisição
            print(f"Falha ao remover imagem antiga {old_image_url}: {e}")

    return ReportOut(
        id=report.id,
        name=report.name,
        title_description=report.title_description,
        description=report.description,
        image_url=report.image_url,
        powerbi_url=report.powerbi_url,
        workspace_id=report.workspace_id,
        report_id=report.report_id,
        group_id=report.group_id,
        is_public=report.is_public,
        access_levels=out_levels,
    )

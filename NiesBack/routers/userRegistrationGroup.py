
from fastapi import APIRouter, Depends, Request,HTTPException
from starlette import status
from fastapi.responses import HTMLResponse
from models.models_rbac import User
from services.security import require_admin
from core.templates import templates
from sqlalchemy.orm import Session, aliased
from db import get_db
from models.models_rbac import User, UserGroup, GroupReportPermission
from models.models import Report, Group
from schemas.schemas_rbac import UserGroupCreate, UserGroupOut
from sqlalchemy import func, distinct
from core.deps import with_menu
from sqlalchemy import select



router = APIRouter(prefix="/register", tags=["register"], dependencies=[Depends(with_menu)])

@router.get("/user-registration-group", response_class=HTMLResponse, include_in_schema=False)
def user_registration_group(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    users_groups = (
        db.query(
            UserGroup.id,
            UserGroup.name,
            UserGroup.description,
            func.count(distinct(GroupReportPermission.report_id)).label("total_reports"),
        )
        .outerjoin(GroupReportPermission, GroupReportPermission.group_id == UserGroup.id)
        .outerjoin(Report, (Report.id == GroupReportPermission.report_id) & (Report.is_active.is_(True)))
        .group_by(UserGroup.id, UserGroup.name)
        .order_by(UserGroup.name.asc())
        .all()
    )
    groups = (
        db.query(Group)
          .filter(Group.is_active.is_(True))
          .order_by(Group.name.asc())
          .all()
    )

    reports = (
        db.query(Report)
          .filter(
              Report.is_active == True
          )
          .order_by(Report.sort_order.is_(None),
                    Report.sort_order.asc(),
                    Report.name.asc())
          .all()
    )

    

    ctx = {
        "request": request,
        "user": user,
        "user_groups": users_groups,
        "groups": groups,
        "reports": reports
    }
    return templates.TemplateResponse("cadastro-grupos.html", ctx)



@router.post("/user-groups", response_model=UserGroupOut, status_code=status.HTTP_201_CREATED)
def create_user_group(
    payload: UserGroupCreate,
    db: Session = Depends(get_db),
    _u: User = Depends(require_admin),
):
    # evita duplicado por nome
    exists = db.query(UserGroup).filter(UserGroup.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=409, detail="Já existe um grupo com esse nome.")

    # valida reports
    if payload.report_ids:
    # 1) Busca somente os IDs existentes no banco
        resultados = (
        db.query(Report.id)
          .filter(Report.id.in_(payload.report_ids))
          .all()
    )

    # 2) Monta um conjunto com os IDs encontrados
    found = set()
    for t in resultados:
        # t pode ser um objeto com atributo .id OU uma tupla (id,)
        if isinstance(t, tuple):
            found.add(t[0])
        else:
            found.add(getattr(t, "id", t))

    # 3) Calcula quais IDs do payload não existem
    missing = set(payload.report_ids) - found

    # 4) Se houver IDs faltando, levanta 400
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Reports inexistentes: {', '.join(sorted(missing))}"
        )

    grp = UserGroup(
        name=payload.name.strip(),
        description=(payload.description or "").strip(),
    )
    db.add(grp)
    db.flush()

    for rep_id in payload.report_ids:
        db.add(GroupReportPermission(group_id=grp.id, report_id=rep_id))

    db.commit()
    db.refresh(grp)

    return UserGroupOut(
        name=grp.name,
        description=grp.description,
        report_ids=payload.report_ids or [],
    )


@router.get("/bi-groups/{group_id}/report-ids")
def report_ids_by_bi_group(
    group_id: str,
    db: Session = Depends(get_db),
    _u: User = Depends(require_admin),
):
    gtbl = Group.__table__

    # CTE recursiva: pega root + descendentes
    cte = select(gtbl.c.id).where(gtbl.c.id == group_id).cte(recursive=True)
    g2 = aliased(gtbl)
    cte = cte.union_all(select(g2.c.id).where(g2.c.parent_id == cte.c.id))

    # Busca reports ativos nesses grupos
    rows = (
        db.query(Report.id)
          .filter(Report.is_active.is_(True),
                  Report.group_id.in_(select(cte.c.id)))
          .all()
    )
    return [r[0] for r in rows]
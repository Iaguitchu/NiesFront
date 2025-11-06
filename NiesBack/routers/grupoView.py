from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse

from db import get_db
from models.models import Group, Report
from models.models_rbac import User, UserGroupMember, GroupReportPermission
from services.security import get_current_user_optional
from core.templates import templates
from core.deps import with_menu

router = APIRouter(prefix="/grupo", tags=["grupo"], dependencies=[Depends(with_menu)])

def build_breadcrumb(db: Session, group: Group) -> list[dict]:
    """Sobe pelos pais até a raiz e devolve [ {id,name}, ... ] """
    gmap = {g.id: g for g in db.query(Group).all()}
    trail = []
    seen = set()
    gid = group.id
    # inclui o atual e vai subindo
    while gid and gid in gmap and gid not in seen:
        gg = gmap[gid]
        trail.append({"id": gg.id, "name": gg.name})
        seen.add(gid)
        gid = gg.parent_id
    trail.reverse()
    return trail

@router.get("/{grupo_id}", response_class=HTMLResponse, include_in_schema=False)
def group_view(
    request: Request,
    grupo_id: str,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    # --- grupo atual ---
    grupo = db.query(Group).filter(Group.id == grupo_id, Group.is_active.is_(True)).first()
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")

    # --- subgrupos (somente 1º nível) ---
    subgrupos = (
        db.query(Group)
          .filter(Group.parent_id == grupo_id, Group.is_active.is_(True))
          .order_by(Group.name.asc())
          .all()
    )

    # --- relatórios do grupo (permissão) ---
    q = db.query(Report).filter(Report.is_active.is_(True), Report.group_id == grupo_id)

    if user and getattr(user, "is_admin", False):
        reports = q.order_by(Report.sort_order.is_(None), Report.sort_order.asc(), Report.name.asc()).all()
    elif user:
        allowed_subq = (
            db.query(GroupReportPermission.report_id)
              .join(UserGroupMember, UserGroupMember.group_id == GroupReportPermission.group_id)
              .filter(UserGroupMember.user_id == user.id)
        )
        reports = (
            q.filter(or_(Report.is_public.is_(True), Report.id.in_(allowed_subq)))
             .order_by(Report.sort_order.is_(None), Report.sort_order.asc(), Report.name.asc())
             .all()
        )
    else:
        reports = (
            q.filter(Report.is_public.is_(True))
             .order_by(Report.sort_order.is_(None), Report.sort_order.asc(), Report.name.asc())
             .all()
        )

    breadcrumb = build_breadcrumb(db, grupo)

    ctx = {
        "request": request,
        "user": user,
        "grupo": grupo,
        "subgrupos": subgrupos,   # cards de navegação pros filhos
        "reports": reports,       # painéis do grupo atual
        "breadcrumb": breadcrumb, # pai → ... → atual
    }
    return templates.TemplateResponse("painel-grupo.html", ctx)

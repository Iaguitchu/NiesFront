from collections import defaultdict, deque
from typing import Dict, List, Set, Any

from sqlalchemy.orm import Session
from sqlalchemy import select
from models.models import Group, Report
from models.models_rbac import User, UserGroupMember, GroupReportPermission


def build_menu_for_user(db: Session, user: User | None) -> List[Dict[str, Any]]:
    """
    Retorna o menu de grupos (apenas 1º nível como raiz),
    filtrando para exibir somente:
      - grupos que possuem ao menos 1 relatório permitido ao usuário em sua subárvore; e
      - os ancestrais desses grupos (para manter a navegação).
    Admin vê tudo.
    """

    # -------- 0) Se admin: mantém seu comportamento atual ----------
    if user and getattr(user, "is_admin", False):
        rows = (
            db.query(Group.id, Group.name, Group.parent_id)
              .filter(Group.is_active.is_(True))
              .all()
        )
        parents, kids = [], defaultdict(list)
        for g in rows:
            item = {"id": g.id, "name": g.name}
            if g.parent_id is None:
                parents.append(item)
            else:
                kids[g.parent_id].append(item)

        parents.sort(key=lambda x: x["name"].lower())
        for v in kids.values():
            v.sort(key=lambda x: x["name"].lower())

        out = []
        for p in parents:
            out.append({
                "id": p["id"],
                "name": p["name"],
                "children": kids.get(p["id"], []),
            })
        return out

    # -------- 1) Mapear toda a árvore de grupos (ativos) ----------
    groups = (
        db.query(Group.id, Group.name, Group.parent_id)
          .filter(Group.is_active.is_(True))
          .all()
    )
    if not groups:
        return []

    name_by_id: Dict[str, str] = {}
    parent_by_id: Dict[str, str | None] = {}
    children_by_id: Dict[str, List[str]] = defaultdict(list)
    top_level_ids: List[str] = []

    for g in groups:
        name_by_id[g.id] = g.name
        parent_by_id[g.id] = g.parent_id
        if g.parent_id is None:
            top_level_ids.append(g.id)
        else:
            children_by_id[g.parent_id].append(g.id)

    # -------- 2) Descobrir quais relatórios o usuário pode ver ----------
    # allowed_report_ids = SELECT report_id FROM GroupReportPermission
    #   JOIN UserGroupMember ON group_id (de usuário) = group_id (do permission)
    #   WHERE UserGroupMember.user_id = user.id
    # OBS: GroupReportPermission.report_id referencia Report.id (string)
    if user is None:
        # usuário anônimo: não vê nada
        allowed_report_ids: Set[str] = set()
    else:
        allowed_subq = (
            db.query(GroupReportPermission.report_id)
              .join(UserGroupMember, UserGroupMember.group_id == GroupReportPermission.group_id)
              .filter(UserGroupMember.user_id == user.id)
              .subquery()
        )
        allowed_report_ids = {
            r[0]
            for r in db.query(Report.id)
                       .filter(Report.is_active.is_(True), Report.id.in_(allowed_subq))
                       .all()
        }

    if not allowed_report_ids:
        # nenhum relatório permitido ⇒ menu vazio
        return []

    # -------- 3) Grupos que possuem RELATÓRIOS PERMITIDOS diretamente ----------
    groups_with_allowed_reports: Set[str] = {
        gid for (gid,) in
        db.query(Report.group_id)
          .filter(Report.is_active.is_(True), Report.id.in_(allowed_report_ids))
          .distinct()
          .all()
    }

    if not groups_with_allowed_reports:
        return []

    # -------- 4) “Bubbling up”: marcar ancestrais desses grupos ----------
    to_include: Set[str] = set()

    def add_ancestors(group_id: str):
        cur = group_id
        while cur is not None and cur in parent_by_id:
            if cur in to_include:
                break
            to_include.add(cur)
            cur = parent_by_id[cur]

    for gid in groups_with_allowed_reports:
        add_ancestors(gid)

    # -------- 5) “Bubbling down”: incluir nós que dão caminho até folhas válidas ----------
    # (Na prática, já incluímos ancestrais. Agora filtraremos as children pelo conjunto to_include)
    # Vamos montar estrutura final: só nós cujo id ∈ to_include.

    # helper para ordenar filhos por nome
    def sort_children(ids: List[str]) -> List[Dict[str, Any]]:
        items = [{"id": cid, "name": name_by_id[cid]} for cid in ids if cid in to_include]
        items.sort(key=lambda x: x["name"].lower())
        return items

    # Primeiro nível: apenas top-level que estejam em to_include
    top_level_items = [{"id": tid, "name": name_by_id[tid]} for tid in top_level_ids if tid in to_include]
    top_level_items.sort(key=lambda x: x["name"].lower())

    # Agora constrói os “children” somente 1 nível (como no seu original)
    resultado: List[Dict[str, Any]] = []
    for p in top_level_items:
        cid_list = children_by_id.get(p["id"], [])
        resultado.append({
            "id": p["id"],
            "name": p["name"],
            "children": sort_children(cid_list),
        })

    # Remove pais que ficaram sem filhos e que NÃO possuem relatório direto (ou descendente)?
    # Como nossa regra já garantiu ancestrais com descendente permitido, podem aparecer pais sem filhos
    # se todo mundo abaixo foi filtrado — isso é raro, mas podemos limpar:
    cleaned: List[Dict[str, Any]] = []
    for node in resultado:
        if node["children"] or node["id"] in groups_with_allowed_reports:
            cleaned.append(node)

    return cleaned

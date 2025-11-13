# core/visibility.py
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session, aliased
from models.models import Group, Report
from models.models_rbac import User, UserGroupMember, GroupReportPermission


def get_visible_children_groups(db: Session, parent_id: str, user: User | None) -> List[Group]:
    """
    Retorna SOMENTE os filhos diretos de `parent_id` cujo SUBTREE contenha
    ao menos 1 Report visível para `user`. Admin vê todos os filhos diretos.
    """
    # Admin: vê todos os filhos diretos
    if user and getattr(user, "is_admin", False):
        return (
            db.query(Group)
              .filter(Group.parent_id == parent_id, Group.is_active.is_(True))
              .order_by(Group.name.asc())
              .all()
        )

    # ---- Reports permitidos ao usuário ----
    if user is None:
        allowed_reports_q = (
            db.query(Report.id)
              .filter(Report.is_active.is_(True), Report.is_public.is_(True))
        )
    else:
        allowed_ids_via_rbac = (
            db.query(GroupReportPermission.report_id)
              .join(UserGroupMember, UserGroupMember.group_id == GroupReportPermission.group_id)
              .filter(UserGroupMember.user_id == user.id)
              .subquery()
        )
        allowed_reports_q = (
            db.query(Report.id)
              .filter(
                  Report.is_active.is_(True),
                  # público OU permitido por RBAC
                  (Report.is_public.is_(True)) | (Report.id.in_(allowed_ids_via_rbac))
              )
        )
    allowed_reports_subq = allowed_reports_q.subquery()

    # grupos que possuem pelo menos 1 desses reports
    groups_with_allowed_reports = (
        db.query(Report.group_id)
          .filter(
              Report.is_active.is_(True),
              Report.id.in_(select(allowed_reports_subq.c.id))
          )
          .distinct()
          .subquery()
    )

    # ---- CTE recursiva do SUBTREE partindo dos FILHOS DIRETOS ----
    # base da CTE: filhos diretos de parent_id
    subtree = (
        select(
            Group.id,
            Group.parent_id,
            Group.id.label("root_child")
        )
        .where(Group.parent_id == parent_id, Group.is_active.is_(True))
        .cte(name="subtree", recursive=True)
    )

    # parte recursiva: filhos dos nós correntes
    G = aliased(Group)  # alias do ORM p/ usar na recursão
    subtree = subtree.union_all(
        select(
            G.id,
            G.parent_id,
            subtree.c.root_child
        )
        .where(G.parent_id == subtree.c.id)
        .where(G.is_active.is_(True))
    )

    # quais root_child têm ALGUM nó do seu subtree com allowed reports
    root_child_ids = (
        db.execute(
            select(subtree.c.root_child)
            .join(
                groups_with_allowed_reports,
                groups_with_allowed_reports.c.group_id == subtree.c.id
            )
            .distinct()
        )
        .scalars()
        .all()
    )

    if not root_child_ids:
        return []

    # retorna somente os filhos diretos filtrados por esses IDs
    return (
        db.query(Group)
          .filter(Group.id.in_(root_child_ids))
          .order_by(Group.name.asc())
          .all()
    )

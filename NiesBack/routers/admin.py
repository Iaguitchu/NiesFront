# routers/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.models_rbac import (
    User, UserStatus,
    UserGroup, UserGroupMember, GroupReportPermission
)
from schemas.schemas_rbac import (
    GroupCreate, GroupOutRBAC, GroupMemberIn, GroupReportPermissionIn, UserOut
)
from services.security import get_current_user_optional

router = APIRouter(prefix="/admin", tags=["admin"])

def require_admin(current = Depends(get_current_user_optional)):
    if not current or not current.is_admin:
        raise HTTPException(403, "Admin only")
    return current

@router.post("/users/{user_id}/approve", response_model=UserOut)
def approve_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    u = db.query(User).get(user_id)
    if not u:
        raise HTTPException(404, "User not found")
    u.status = UserStatus.approved
    db.commit(); db.refresh(u)
    return u

@router.post("/groups", response_model=GroupOutRBAC)
def create_group(data: GroupCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    g = UserGroup(name=data.name, description=data.description)
    db.add(g); db.commit(); db.refresh(g)
    return g

@router.post("/groups/{group_id}/members")
def add_member(group_id: int, m: GroupMemberIn, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if not db.query(UserGroup).get(group_id):
        raise HTTPException(404, "Group not found")
    if not db.query(User).get(m.user_id):
        raise HTTPException(404, "User not found")
    exists = db.query(UserGroupMember).filter_by(group_id=group_id, user_id=m.user_id).first()
    if exists: return {"ok": True}
    db.add(UserGroupMember(group_id=group_id, user_id=m.user_id)); db.commit()
    return {"ok": True}

@router.post("/groups/{group_id}/report-permissions")
def grant_report(group_id: int, body: GroupReportPermissionIn, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if not db.query(UserGroup).get(group_id):
        raise HTTPException(404, "Group not found")
    exists = db.query(GroupReportPermission).filter_by(group_id=group_id, report_id=body.report_id).first()
    if exists: return {"ok": True}
    db.add(GroupReportPermission(group_id=group_id, report_id=body.report_id)); db.commit()
    return {"ok": True}

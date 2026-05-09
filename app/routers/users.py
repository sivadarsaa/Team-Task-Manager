from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.activity import record_activity
from app.deps import get_db, get_current_user, require_system_admin
from app.enums import UserRole
from app.models import User
from app.schemas import UserPublic, UserRoleUpdate


router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserPublic])
def list_users(_: User = Depends(require_system_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.asc()).all()
    return [UserPublic.model_validate(user) for user in users]


@router.patch("/{user_id}/role", response_model=UserPublic)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager access is required for this action.")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if target_user.role == UserRole.manager and payload.role != UserRole.manager:
        manager_count = db.query(User).filter(User.role == UserRole.manager).count()
        if manager_count <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one manager must remain.")

    target_user.role = payload.role
    record_activity(
        db,
        actor=current_user,
        action="user.role_updated",
        description=f"{current_user.full_name} changed {target_user.full_name}'s system role to {payload.role.value}.",
    )
    db.commit()
    db.refresh(target_user)
    return UserPublic.model_validate(target_user)

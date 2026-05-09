from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.deps import get_current_user, get_db
from app.enums import UserRole
from app.models import Activity, ProjectMembership, Task, User
from app.schemas import ActivityOut


router = APIRouter(prefix="/api/activity", tags=["activity"])


@router.get("", response_model=list[ActivityOut])
def list_activity(
    limit: int = Query(default=20, ge=1, le=100),
    project_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Activity).options(joinedload(Activity.actor)).order_by(Activity.created_at.desc())

    if project_id is not None:
        query = query.filter(Activity.project_id == project_id)

    if current_user.role != UserRole.manager:
        project_ids = [
            pid
            for (pid,) in db.query(ProjectMembership.project_id).filter(ProjectMembership.user_id == current_user.id).all()
        ]
        assigned_task_ids = [
            task_id for (task_id,) in db.query(Task.id).filter(Task.assigned_to_id == current_user.id).all()
        ]
        query = query.filter(
            or_(
                Activity.actor_id == current_user.id,
                Activity.project_id.in_(project_ids or [-1]),
                Activity.task_id.in_(assigned_task_ids or [-1]),
            )
        )

    return [ActivityOut.model_validate(item) for item in query.limit(limit).all()]

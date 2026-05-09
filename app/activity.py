from sqlalchemy.orm import Session

from app.models import Activity, Project, Task, User


def record_activity(
    db: Session,
    *,
    actor: User,
    action: str,
    description: str,
    project: Project | None = None,
    task: Task | None = None,
) -> Activity:
    activity = Activity(
        actor_id=actor.id,
        project_id=project.id if project else None,
        task_id=task.id if task else None,
        action=action,
        description=description,
    )
    db.add(activity)
    return activity

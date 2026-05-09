from collections import Counter
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.deps import get_current_user, get_db
from app.enums import TaskStatus, UserRole
from app.models import Activity, Project, ProjectMembership, Task, User
from app.schemas import (
    ActivityOut,
    AnalyticsOverview,
    ChartPoint,
    DashboardOverview,
    DashboardStats,
    ProjectProgressPoint,
    TaskOut,
    TeamWorkloadPoint,
)


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def get_accessible_project_ids(db: Session, current_user: User) -> list[int]:
    if current_user.role == UserRole.manager:
        return [project_id for (project_id,) in db.query(Project.id).all()]
    return [
        project_id
        for (project_id,) in db.query(ProjectMembership.project_id).filter(ProjectMembership.user_id == current_user.id).all()
    ]


def get_accessible_tasks_query(db: Session, current_user: User):
    query = db.query(Task).options(joinedload(Task.assigned_to), joinedload(Task.created_by))
    if current_user.role == UserRole.manager:
        return query
    return query.filter(Task.assigned_to_id == current_user.id)


def get_recent_activity(db: Session, current_user: User, limit: int = 12) -> list[Activity]:
    query = db.query(Activity).options(joinedload(Activity.actor)).order_by(Activity.created_at.desc())
    if current_user.role == UserRole.manager:
        return query.limit(limit).all()

    project_ids = get_accessible_project_ids(db, current_user)
    assigned_task_ids = [
        task_id for (task_id,) in db.query(Task.id).filter(Task.assigned_to_id == current_user.id).all()
    ]

    if not project_ids and not assigned_task_ids:
        return query.filter(Activity.actor_id == current_user.id).limit(limit).all()

    return (
        query.filter(
            or_(
                Activity.actor_id == current_user.id,
                Activity.project_id.in_(project_ids or [-1]),
                Activity.task_id.in_(assigned_task_ids or [-1]),
            )
        )
        .limit(limit)
        .all()
    )


@router.get("", response_model=DashboardOverview)
def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    assigned_tasks = (
        db.query(Task)
        .options(joinedload(Task.assigned_to), joinedload(Task.created_by))
        .filter(Task.assigned_to_id == current_user.id)
        .order_by(Task.due_date.is_(None), Task.due_date.asc(), Task.updated_at.desc())
        .all()
    )
    today = date.today()
    overdue_tasks = [task for task in assigned_tasks if task.due_date and task.due_date < today and task.status != TaskStatus.done]
    accessible_tasks = (
        get_accessible_tasks_query(db, current_user)
        .order_by(Task.updated_at.desc(), Task.created_at.desc())
        .all()
    )
    stats_tasks = accessible_tasks if current_user.role == UserRole.manager else assigned_tasks
    overdue_stats_tasks = [
        task for task in stats_tasks if task.due_date and task.due_date < today and task.status != TaskStatus.done
    ]
    upcoming_deadlines = [
        task
        for task in sorted(
            accessible_tasks,
            key=lambda item: (item.due_date is None, item.due_date or date.max, -item.id),
        )
        if task.due_date and task.status != TaskStatus.done
    ][:6]

    stats = DashboardStats(
        total_assigned=len(stats_tasks),
        todo=sum(1 for task in stats_tasks if task.status == TaskStatus.todo),
        in_progress=sum(1 for task in stats_tasks if task.status == TaskStatus.in_progress),
        done=sum(1 for task in stats_tasks if task.status == TaskStatus.done),
        overdue=len(overdue_stats_tasks),
        projects=db.query(ProjectMembership).filter(ProjectMembership.user_id == current_user.id).count()
        if current_user.role != UserRole.manager
        else db.query(Project).count(),
    )
    return DashboardOverview(
        stats=stats,
        assigned_tasks=[TaskOut.model_validate(task) for task in assigned_tasks[:8]],
        overdue_tasks=[TaskOut.model_validate(task) for task in overdue_tasks[:8]],
        recent_tasks=[TaskOut.model_validate(task) for task in accessible_tasks[:8]],
        upcoming_deadlines=[TaskOut.model_validate(task) for task in upcoming_deadlines],
        recent_activity=[ActivityOut.model_validate(activity) for activity in get_recent_activity(db, current_user)],
    )


@router.get("/analytics", response_model=AnalyticsOverview)
def get_analytics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accessible_project_ids = get_accessible_project_ids(db, current_user)
    accessible_tasks = (
        get_accessible_tasks_query(db, current_user)
        .order_by(Task.created_at.asc())
        .all()
    )
    today = date.today()
    start_of_window = today - timedelta(days=35)

    weekly_points: list[ChartPoint] = []
    for offset in range(6):
        week_start = start_of_window + timedelta(days=offset * 7)
        week_end = week_start + timedelta(days=6)
        value = sum(
            1
            for task in accessible_tasks
            if task.status == TaskStatus.done and task.updated_at.date() >= week_start and task.updated_at.date() <= week_end
        )
        weekly_points.append(ChartPoint(label=week_start.strftime("%b %d"), value=value))

    status_counts = Counter(task.status.value for task in accessible_tasks)
    productivity = [
        ChartPoint(label="To do", value=status_counts.get(TaskStatus.todo.value, 0)),
        ChartPoint(label="In progress", value=status_counts.get(TaskStatus.in_progress.value, 0)),
        ChartPoint(label="Done", value=status_counts.get(TaskStatus.done.value, 0)),
    ]

    overdue_chart = [
        ChartPoint(
            label="Overdue",
            value=sum(1 for task in accessible_tasks if task.due_date and task.due_date < today and task.status != TaskStatus.done),
        ),
        ChartPoint(
            label="Due soon",
            value=sum(
                1
                for task in accessible_tasks
                if task.due_date and today <= task.due_date <= today + timedelta(days=7) and task.status != TaskStatus.done
            ),
        ),
        ChartPoint(
            label="On track",
            value=sum(
                1
                for task in accessible_tasks
                if not task.due_date or task.due_date > today + timedelta(days=7) or task.status == TaskStatus.done
            ),
        ),
    ]

    if current_user.role == UserRole.manager:
        workload_users = (
            db.query(User)
            .outerjoin(Task, Task.assigned_to_id == User.id)
            .filter(User.role.in_([UserRole.manager, UserRole.employee]))
            .order_by(User.full_name.asc())
            .all()
        )
    else:
        workload_users = [current_user]

    team_workload: list[TeamWorkloadPoint] = []
    for user in workload_users:
        user_tasks = [task for task in accessible_tasks if task.assigned_to_id == user.id]
        if current_user.role != UserRole.manager and user.id != current_user.id:
            continue
        team_workload.append(
            TeamWorkloadPoint(
                label=user.full_name,
                todo=sum(1 for task in user_tasks if task.status == TaskStatus.todo),
                in_progress=sum(1 for task in user_tasks if task.status == TaskStatus.in_progress),
                done=sum(1 for task in user_tasks if task.status == TaskStatus.done),
                total=len(user_tasks),
            )
        )

    project_progress: list[ProjectProgressPoint] = []
    for project in (
        db.query(Project)
        .options(joinedload(Project.tasks))
        .filter(Project.id.in_(accessible_project_ids or [-1]))
        .order_by(Project.created_at.desc())
        .all()
    ):
        project_tasks = project.tasks if current_user.role == UserRole.manager else [task for task in project.tasks if task.assigned_to_id == current_user.id]
        total = len(project_tasks)
        done_count = sum(1 for task in project_tasks if task.status == TaskStatus.done)
        in_progress_count = sum(1 for task in project_tasks if task.status == TaskStatus.in_progress)
        todo_count = sum(1 for task in project_tasks if task.status == TaskStatus.todo)
        completion_rate = int((done_count / total) * 100) if total else 0
        project_progress.append(
            ProjectProgressPoint(
                label=project.name,
                todo=todo_count,
                in_progress=in_progress_count,
                done=done_count,
                total=total,
                completion_rate=completion_rate,
            )
        )

    return AnalyticsOverview(
        completed_tasks_per_week=weekly_points,
        productivity=productivity,
        overdue_tasks=overdue_chart,
        team_workload=team_workload,
        project_progress=project_progress,
    )

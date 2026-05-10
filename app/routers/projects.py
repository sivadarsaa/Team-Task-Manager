from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.activity import record_activity
from app.deps import get_current_user, get_db
from app.enums import MembershipRole, TaskPriority, TaskStatus, UserRole
from app.models import Project, ProjectMembership, Task, User
from app.schemas import (
    MemberInvite,
    MemberRoleUpdate,
    PermissionSet,
    ProjectCreate,
    ProjectDetail,
    ProjectMembershipOut,
    ProjectSummary,
    TaskCreate,
    TaskOut,
    TaskUpdate,
    UserPublic,
)


router = APIRouter(prefix="/api/projects", tags=["projects"])


def build_permissions(current_user: User) -> PermissionSet:
    is_manager = current_user.role == UserRole.manager
    return PermissionSet(
        can_create_projects=is_manager,
        can_delete_projects=is_manager,
        can_manage_members=is_manager,
        can_manage_roles=is_manager,
        can_assign_tasks=is_manager,
        can_view_all_tasks=is_manager,
        can_update_assigned_tasks=True,
    )


def require_manager(current_user: User) -> None:
    if current_user.role != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager access is required for this action.")


def get_project_membership(db: Session, project_id: int, user_id: int) -> ProjectMembership | None:
    return (
        db.query(ProjectMembership)
        .options(joinedload(ProjectMembership.project).joinedload(Project.owner))
        .filter(ProjectMembership.project_id == project_id, ProjectMembership.user_id == user_id)
        .first()
    )


def get_project_role(db: Session, project_id: int, current_user: User) -> MembershipRole:
    membership = get_project_membership(db, project_id, current_user.id)
    if membership:
        return membership.role

    project_exists = db.query(Project.id).filter(Project.id == project_id).first()
    if not project_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if current_user.role == UserRole.manager:
        return MembershipRole.admin

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")


def get_accessible_project(db: Session, project_id: int, current_user: User) -> Project:
    get_project_role(db, project_id, current_user)
    project = (
        db.query(Project)
        .options(
            joinedload(Project.owner),
            joinedload(Project.memberships).joinedload(ProjectMembership.user),
            joinedload(Project.tasks).joinedload(Task.assigned_to),
            joinedload(Project.tasks).joinedload(Task.created_by),
        )
        .filter(Project.id == project_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


def serialize_project_summary(project: Project, role: MembershipRole, current_user: User) -> ProjectSummary:
    visible_tasks = project.tasks if current_user.role == UserRole.manager else [task for task in project.tasks if task.assigned_to_id == current_user.id]
    counts = Counter(task.status.value for task in visible_tasks)
    return ProjectSummary(
        id=project.id,
        name=project.name,
        description=project.description,
        due_date=project.due_date,
        created_at=project.created_at,
        current_role=role,
        owner=UserPublic.model_validate(project.owner),
        member_count=len(project.memberships),
        task_counts={
            TaskStatus.todo.value: counts.get(TaskStatus.todo.value, 0),
            TaskStatus.in_progress.value: counts.get(TaskStatus.in_progress.value, 0),
            TaskStatus.done.value: counts.get(TaskStatus.done.value, 0),
        },
        permissions=build_permissions(current_user),
    )


@router.get("", response_model=list[ProjectSummary])
def list_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == UserRole.manager:
        projects = (
            db.query(Project)
            .options(joinedload(Project.owner), joinedload(Project.memberships), joinedload(Project.tasks))
            .order_by(Project.created_at.desc())
            .all()
        )
        return [serialize_project_summary(project, MembershipRole.admin, current_user) for project in projects]

    memberships = (
        db.query(ProjectMembership)
        .options(
            joinedload(ProjectMembership.project).joinedload(Project.owner),
            joinedload(ProjectMembership.project).joinedload(Project.memberships),
            joinedload(ProjectMembership.project).joinedload(Project.tasks),
        )
        .filter(ProjectMembership.user_id == current_user.id)
        .all()
    )
    return [serialize_project_summary(item.project, item.role, current_user) for item in memberships]


@router.post("", response_model=ProjectSummary, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager(current_user)

    project = Project(
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        due_date=payload.due_date,
        owner_id=current_user.id,
    )
    db.add(project)
    db.flush()

    membership = ProjectMembership(project_id=project.id, user_id=current_user.id, role=MembershipRole.admin)
    db.add(membership)
    record_activity(
        db,
        actor=current_user,
        project=project,
        action="project.created",
        description=f"{current_user.full_name} created project {project.name}.",
    )
    db.commit()

    project = (
        db.query(Project)
        .options(joinedload(Project.owner), joinedload(Project.memberships), joinedload(Project.tasks))
        .filter(Project.id == project.id)
        .first()
    )
    return serialize_project_summary(project, MembershipRole.admin, current_user)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager(current_user)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    record_activity(
        db,
        actor=current_user,
        action="project.deleted",
        description=f"{current_user.full_name} deleted project {project.name}.",
    )
    db.flush()
    db.delete(project)
    db.commit()


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project_detail(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    effective_role = get_project_role(db, project_id, current_user)
    project = get_accessible_project(db, project_id, current_user)
    tasks = project.tasks if current_user.role == UserRole.manager else [task for task in project.tasks if task.assigned_to_id == current_user.id]
    return ProjectDetail(
        id=project.id,
        name=project.name,
        description=project.description,
        due_date=project.due_date,
        created_at=project.created_at,
        current_role=effective_role,
        owner=UserPublic.model_validate(project.owner),
        members=[ProjectMembershipOut.model_validate(item) for item in project.memberships],
        tasks=[TaskOut.model_validate(task) for task in tasks],
        permissions=build_permissions(current_user),
    )


@router.post("/{project_id}/members", response_model=ProjectMembershipOut, status_code=status.HTTP_201_CREATED)
def add_member(
    project_id: int,
    payload: MemberInvite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_manager(current_user)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email does not exist.")

    existing_membership = (
        db.query(ProjectMembership)
        .filter(ProjectMembership.project_id == project_id, ProjectMembership.user_id == user.id)
        .first()
    )
    if existing_membership:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this project.")

    new_membership = ProjectMembership(project_id=project_id, user_id=user.id, role=payload.role)
    db.add(new_membership)
    record_activity(
        db,
        actor=current_user,
        project=project,
        action="member.added",
        description=f"{current_user.full_name} added {user.full_name} to {project.name}.",
    )
    db.commit()
    db.refresh(new_membership)
    return ProjectMembershipOut.model_validate(new_membership)


@router.patch("/{project_id}/members/{member_user_id}", response_model=ProjectMembershipOut)
def update_member_role(
    project_id: int,
    member_user_id: int,
    payload: MemberRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_manager(current_user)

    target_membership = (
        db.query(ProjectMembership)
        .options(joinedload(ProjectMembership.user))
        .filter(ProjectMembership.project_id == project_id, ProjectMembership.user_id == member_user_id)
        .first()
    )
    if not target_membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found.")

    project = db.query(Project).filter(Project.id == project_id).first()
    if project.owner_id == member_user_id and payload.role != MembershipRole.admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project owner must remain an admin.")

    target_membership.role = payload.role
    record_activity(
        db,
        actor=current_user,
        project=project,
        action="member.role_updated",
        description=f"{current_user.full_name} changed {target_membership.user.full_name}'s role in {project.name}.",
    )
    db.commit()
    db.refresh(target_membership)
    return ProjectMembershipOut.model_validate(target_membership)


@router.delete("/{project_id}/members/{member_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    project_id: int,
    member_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_manager(current_user)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if project.owner_id == member_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project owner cannot be removed.")

    target_membership = (
        db.query(ProjectMembership)
        .options(joinedload(ProjectMembership.user))
        .filter(ProjectMembership.project_id == project_id, ProjectMembership.user_id == member_user_id)
        .first()
    )
    if not target_membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found.")

    record_activity(
        db,
        actor=current_user,
        project=project,
        action="member.removed",
        description=f"{current_user.full_name} removed {target_membership.user.full_name} from {project.name}.",
    )
    db.delete(target_membership)
    db.commit()


@router.get("/{project_id}/tasks", response_model=list[TaskOut])
def list_project_tasks(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_project_role(db, project_id, current_user)
    query = (
        db.query(Task)
        .options(joinedload(Task.assigned_to), joinedload(Task.created_by))
        .filter(Task.project_id == project_id)
        .order_by(Task.due_date.is_(None), Task.due_date.asc(), Task.created_at.desc())
    )
    if current_user.role != UserRole.manager:
        query = query.filter(Task.assigned_to_id == current_user.id)
    tasks = query.all()
    return [TaskOut.model_validate(task) for task in tasks]


@router.post("/{project_id}/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    project_id: int,
    payload: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_manager(current_user)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if payload.assigned_to_id is not None:
        assignee_membership = (
            db.query(ProjectMembership)
            .filter(ProjectMembership.project_id == project_id, ProjectMembership.user_id == payload.assigned_to_id)
            .first()
        )
        if not assignee_membership:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assignee must be a member of the project.")

    task = Task(
        project_id=project_id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        priority=payload.priority,
        due_date=payload.due_date,
        assigned_to_id=payload.assigned_to_id,
        created_by_id=current_user.id,
    )
    db.add(task)
    db.flush()
    record_activity(
        db,
        actor=current_user,
        project=project,
        task=task,
        action="task.created",
        description=f"{current_user.full_name} created task {task.title}.",
    )
    db.commit()
    task = (
        db.query(Task)
        .options(joinedload(Task.assigned_to), joinedload(Task.created_by))
        .filter(Task.id == task.id)
        .first()
    )
    return TaskOut.model_validate(task)


@router.patch("/{project_id}/tasks/{task_id}", response_model=TaskOut)
def update_task(
    project_id: int,
    task_id: int,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_project_role(db, project_id, current_user)
    task = (
        db.query(Task)
        .options(joinedload(Task.assigned_to), joinedload(Task.created_by), joinedload(Task.project))
        .filter(Task.project_id == project_id, Task.id == task_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    updates = payload.model_dump(exclude_unset=True)
    is_manager = current_user.role == UserRole.manager
    if not is_manager:
        allowed_keys = {"status"}
        if task.assigned_to_id != current_user.id or set(updates.keys()) - allowed_keys:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Members can only update the status of tasks assigned to them.",
            )

    if "assigned_to_id" in updates and updates["assigned_to_id"] is not None:
        assignee_membership = (
            db.query(ProjectMembership)
            .filter(ProjectMembership.project_id == project_id, ProjectMembership.user_id == updates["assigned_to_id"])
            .first()
        )
        if not assignee_membership:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assignee must be a member of the project.")

    original_status = task.status
    enum_fields = {
        "status": TaskStatus,
        "priority": TaskPriority,
    }
    for field, value in updates.items():
        enum_type = enum_fields.get(field)
        if enum_type and isinstance(value, str):
            value = enum_type(value)
        elif isinstance(value, str):
            value = value.strip()
        setattr(task, field, value)

    if updates:
        status_label = task.status.value if isinstance(task.status, TaskStatus) else str(task.status)
        if "status" in updates and updates["status"] != original_status:
            record_activity(
                db,
                actor=current_user,
                project=task.project,
                task=task,
                action="task.status_updated",
                description=f"{current_user.full_name} moved task {task.title} to {status_label.replace('_', ' ')}.",
            )
        else:
            record_activity(
                db,
                actor=current_user,
                project=task.project,
                task=task,
                action="task.updated",
                description=f"{current_user.full_name} updated task {task.title}.",
            )

    db.commit()
    db.refresh(task)
    return TaskOut.model_validate(task)


@router.delete("/{project_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    project_id: int,
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_manager(current_user)

    task = (
        db.query(Task)
        .options(joinedload(Task.project))
        .filter(Task.project_id == project_id, Task.id == task_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    record_activity(
        db,
        actor=current_user,
        action="task.deleted",
        description=f"{current_user.full_name} deleted task {task.title}.",
    )
    db.delete(task)
    db.commit()

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.activity import record_activity
from app.auth import get_password_hash
from app.config import get_settings
from app.database import Base, SessionLocal, database_url, engine, ensure_database_storage
from app.enums import MembershipRole, TaskPriority, TaskStatus, UserRole
from app.models import Activity, Project, ProjectMembership, Task, User


settings = get_settings()

DEMO_USERS = [
    {
        "full_name": "Olivia Chen",
        "email": "olivia.chen.manager@example.com",
        "role": UserRole.manager,
    },
    {
        "full_name": "Priya Nair",
        "email": "priya.nair@example.com",
        "role": UserRole.employee,
    },
    {
        "full_name": "Arjun Patel",
        "email": "arjun.patel@example.com",
        "role": UserRole.employee,
    },
    {
        "full_name": "Meera Joshi",
        "email": "meera.joshi@example.com",
        "role": UserRole.employee,
    },
    {
        "full_name": "Daniel Kim",
        "email": "daniel.kim@example.com",
        "role": UserRole.employee,
    },
]


def build_demo_projects(today: date) -> list[dict]:
    return [
        {
            "name": "Website Relaunch",
            "description": "Refresh the public site, tighten the launch checklist, and close final QA before rollout.",
            "due_date": today + timedelta(days=21),
            "owner_email": "olivia.chen.manager@example.com",
            "members": [
                {"email": "priya.nair@example.com", "role": MembershipRole.member},
                {"email": "daniel.kim@example.com", "role": MembershipRole.member},
                {"email": "g@gmail.com", "role": MembershipRole.member},
            ],
            "tasks": [
                {
                    "title": "Finalize sitemap review",
                    "description": "Confirm the final page hierarchy and navigation labels.",
                    "status": TaskStatus.done,
                    "priority": TaskPriority.medium,
                    "due_date": today - timedelta(days=5),
                    "assigned_to_email": "olivia.chen.manager@example.com",
                    "created_by_email": "olivia.chen.manager@example.com",
                },
                {
                    "title": "Build marketing hero section",
                    "description": "Implement the updated hero layout with the revised CTA copy.",
                    "status": TaskStatus.in_progress,
                    "priority": TaskPriority.high,
                    "due_date": today + timedelta(days=4),
                    "assigned_to_email": "priya.nair@example.com",
                    "created_by_email": "olivia.chen.manager@example.com",
                },
                {
                    "title": "QA responsive layout pass",
                    "description": "Test the new homepage on tablet and mobile breakpoints.",
                    "status": TaskStatus.todo,
                    "priority": TaskPriority.medium,
                    "due_date": today + timedelta(days=8),
                    "assigned_to_email": "daniel.kim@example.com",
                    "created_by_email": "priya.nair@example.com",
                },
                {
                    "title": "Prepare launch checklist",
                    "description": "Collect the final pre-launch tasks for content, analytics, and support.",
                    "status": TaskStatus.todo,
                    "priority": TaskPriority.low,
                    "due_date": today + timedelta(days=10),
                    "assigned_to_email": None,
                    "created_by_email": "olivia.chen.manager@example.com",
                },
            ],
        },
        {
            "name": "Mobile App Sprint",
            "description": "Deliver the next sprint with bug fixes, onboarding polish, and release prep.",
            "due_date": today + timedelta(days=28),
            "owner_email": "olivia.chen.manager@example.com",
            "members": [
                {"email": "arjun.patel@example.com", "role": MembershipRole.member},
                {"email": "meera.joshi@example.com", "role": MembershipRole.member},
                {"email": "priya.nair@example.com", "role": MembershipRole.member},
            ],
            "tasks": [
                {
                    "title": "Fix login session timeout bug",
                    "description": "Resolve the unexpected logout issue happening during longer sessions.",
                    "status": TaskStatus.in_progress,
                    "priority": TaskPriority.high,
                    "due_date": today - timedelta(days=2),
                    "assigned_to_email": "arjun.patel@example.com",
                    "created_by_email": "olivia.chen.manager@example.com",
                },
                {
                    "title": "Implement notification preferences",
                    "description": "Add per-user notification toggles for push and email alerts.",
                    "status": TaskStatus.todo,
                    "priority": TaskPriority.medium,
                    "due_date": today + timedelta(days=6),
                    "assigned_to_email": "meera.joshi@example.com",
                    "created_by_email": "olivia.chen.manager@example.com",
                },
                {
                    "title": "Review onboarding copy",
                    "description": "Tighten the microcopy in the first-run onboarding screens.",
                    "status": TaskStatus.done,
                    "priority": TaskPriority.low,
                    "due_date": today - timedelta(days=1),
                    "assigned_to_email": "priya.nair@example.com",
                    "created_by_email": "meera.joshi@example.com",
                },
                {
                    "title": "Draft release notes",
                    "description": "Prepare the internal release note summary for support and QA teams.",
                    "status": TaskStatus.todo,
                    "priority": TaskPriority.low,
                    "due_date": today + timedelta(days=9),
                    "assigned_to_email": None,
                    "created_by_email": "olivia.chen.manager@example.com",
                },
            ],
        },
        {
            "name": "Operations Cleanup",
            "description": "Tidy recurring operations work, close stale gaps, and keep admin work visible.",
            "due_date": today + timedelta(days=18),
            "owner_email": "olivia.chen.manager@example.com",
            "members": [
                {"email": "daniel.kim@example.com", "role": MembershipRole.member},
                {"email": "meera.joshi@example.com", "role": MembershipRole.member},
                {"email": "g@gmail.com", "role": MembershipRole.member},
            ],
            "tasks": [
                {
                    "title": "Audit inactive user accounts",
                    "description": "Flag dormant accounts and prepare the deactivation list.",
                    "status": TaskStatus.todo,
                    "priority": TaskPriority.high,
                    "due_date": today + timedelta(days=3),
                    "assigned_to_email": "daniel.kim@example.com",
                    "created_by_email": "olivia.chen.manager@example.com",
                },
                {
                    "title": "Clean backlog labels",
                    "description": "Normalize task labels across the shared operations backlog.",
                    "status": TaskStatus.in_progress,
                    "priority": TaskPriority.low,
                    "due_date": today + timedelta(days=7),
                    "assigned_to_email": "meera.joshi@example.com",
                    "created_by_email": "olivia.chen.manager@example.com",
                },
                {
                    "title": "Update vendor renewal tracker",
                    "description": "Bring subscription renewals and owner notes up to date.",
                    "status": TaskStatus.done,
                    "priority": TaskPriority.medium,
                    "due_date": today - timedelta(days=3),
                    "assigned_to_email": "olivia.chen.manager@example.com",
                    "created_by_email": "olivia.chen.manager@example.com",
                },
            ],
        },
    ]


def get_or_create_user(
    db: Session,
    users_by_email: dict[str, User],
    *,
    full_name: str,
    email: str,
    role: UserRole,
    summary: dict[str, int],
) -> User:
    existing = users_by_email.get(email)
    if existing:
        return existing

    user = User(
        full_name=full_name,
        email=email,
        password_hash=get_password_hash(settings.demo_password),
        role=role,
    )
    db.add(user)
    db.flush()
    users_by_email[email] = user
    summary["users"] += 1
    return user


def ensure_membership(
    db: Session,
    *,
    project_id: int,
    user_id: int,
    role: MembershipRole,
    summary: dict[str, int],
) -> None:
    existing = (
        db.query(ProjectMembership)
        .filter(ProjectMembership.project_id == project_id, ProjectMembership.user_id == user_id)
        .first()
    )
    if existing:
        if existing.role != role:
            existing.role = role
        return

    db.add(ProjectMembership(project_id=project_id, user_id=user_id, role=role))
    summary["memberships"] += 1


def ensure_task(
    db: Session,
    *,
    project_id: int,
    title: str,
    description: str,
    status: TaskStatus,
    priority: TaskPriority,
    due_date: date | None,
    assigned_to_id: int | None,
    created_by_id: int,
    summary: dict[str, int],
) -> None:
    existing = db.query(Task).filter(Task.project_id == project_id, Task.title == title).first()
    if existing:
        return

    db.add(
        Task(
            project_id=project_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            due_date=due_date,
            assigned_to_id=assigned_to_id,
            created_by_id=created_by_id,
        )
    )
    summary["tasks"] += 1


def seed_demo_data(db: Session) -> dict[str, int]:
    if not settings.demo_password:
        raise RuntimeError("Set DEMO_PASSWORD in your environment before running the seed script.")

    summary = {"users": 0, "projects": 0, "memberships": 0, "tasks": 0}
    users_by_email = {user.email: user for user in db.query(User).all()}

    for user_data in DEMO_USERS:
        get_or_create_user(db, users_by_email, summary=summary, **user_data)

    demo_projects = build_demo_projects(date.today())
    existing_projects = {project.name: project for project in db.query(Project).all()}

    for project_data in demo_projects:
        owner = users_by_email[project_data["owner_email"]]
        project = existing_projects.get(project_data["name"])
        if project is None:
            project = Project(
                name=project_data["name"],
                description=project_data["description"],
                due_date=project_data["due_date"],
                owner_id=owner.id,
            )
            db.add(project)
            db.flush()
            existing_projects[project.name] = project
            summary["projects"] += 1

        ensure_membership(
            db,
            project_id=project.id,
            user_id=owner.id,
            role=MembershipRole.admin,
            summary=summary,
        )

        for member_data in project_data["members"]:
            member = users_by_email.get(member_data["email"])
            if member is None:
                continue
            ensure_membership(
                db,
                project_id=project.id,
                user_id=member.id,
                role=member_data["role"],
                summary=summary,
            )

        for task_data in project_data["tasks"]:
            assignee = users_by_email.get(task_data["assigned_to_email"]) if task_data["assigned_to_email"] else None
            creator = users_by_email[task_data["created_by_email"]]
            ensure_task(
                db,
                project_id=project.id,
                title=task_data["title"],
                description=task_data["description"],
                status=task_data["status"],
                priority=task_data["priority"],
                due_date=task_data["due_date"],
                assigned_to_id=assignee.id if assignee else None,
                created_by_id=creator.id,
                summary=summary,
            )

    db.commit()

    if db.query(Activity).count() == 0:
        manager = users_by_email.get("olivia.chen.manager@example.com")
        if manager:
            for project in db.query(Project).order_by(Project.created_at.asc()).all():
                record_activity(
                    db,
                    actor=manager,
                    project=project,
                    action="project.created",
                    description=f"{manager.full_name} created project {project.name}.",
                )
            for task in db.query(Task).order_by(Task.created_at.asc()).all():
                actor = task.created_by or manager
                message = (
                    f"{actor.full_name} completed task {task.title}."
                    if task.status == TaskStatus.done
                    else f"{actor.full_name} created task {task.title}."
                )
                action = "task.status_updated" if task.status == TaskStatus.done else "task.created"
                record_activity(
                    db,
                    actor=actor,
                    project=task.project,
                    task=task,
                    action=action,
                    description=message,
                )
        db.commit()

    return summary


def main() -> None:
    ensure_database_storage(database_url)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        summary = seed_demo_data(db)
        totals = {
            "users": db.query(User).count(),
            "projects": db.query(Project).count(),
            "memberships": db.query(ProjectMembership).count(),
            "tasks": db.query(Task).count(),
        }

    print("Seed summary:", summary)
    print("Current totals:", totals)
    print("Demo password:", settings.demo_password)


if __name__ == "__main__":
    main()

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import MembershipRole, TaskPriority, TaskStatus, UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, native_enum=False), default=UserRole.employee, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    owned_projects: Mapped[list["Project"]] = relationship(back_populates="owner")
    memberships: Mapped[list["ProjectMembership"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    assigned_tasks: Mapped[list["Task"]] = relationship(foreign_keys="Task.assigned_to_id", back_populates="assigned_to")
    created_tasks: Mapped[list["Task"]] = relationship(foreign_keys="Task.created_by_id", back_populates="created_by")
    activities: Mapped[list["Activity"]] = relationship(back_populates="actor")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    owner: Mapped["User"] = relationship(back_populates="owned_projects")
    memberships: Mapped[list["ProjectMembership"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    tasks: Mapped[list["Task"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    activities: Mapped[list["Activity"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class ProjectMembership(Base):
    __tablename__ = "project_memberships"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_membership"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[MembershipRole] = mapped_column(Enum(MembershipRole, native_enum=False), default=MembershipRole.member, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="memberships")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus, native_enum=False), default=TaskStatus.todo, nullable=False)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority, native_enum=False), default=TaskPriority.medium, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="tasks")
    assigned_to: Mapped["User | None"] = relationship(foreign_keys=[assigned_to_id], back_populates="assigned_tasks")
    created_by: Mapped["User"] = relationship(foreign_keys=[created_by_id], back_populates="created_tasks")
    activities: Mapped[list["Activity"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    actor: Mapped["User"] = relationship(back_populates="activities")
    project: Mapped["Project | None"] = relationship(back_populates="activities")
    task: Mapped["Task | None"] = relationship(back_populates="activities")

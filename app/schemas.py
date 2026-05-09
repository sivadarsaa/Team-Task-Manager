from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.enums import MembershipRole, TaskPriority, TaskStatus, UserRole


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.employee

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower().strip()


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    expected_role: UserRole | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower().strip()


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    created_at: datetime


class PermissionSet(BaseModel):
    can_create_projects: bool = False
    can_delete_projects: bool = False
    can_manage_members: bool = False
    can_manage_roles: bool = False
    can_assign_tasks: bool = False
    can_view_all_tasks: bool = False
    can_update_assigned_tasks: bool = False


class AuthResponse(BaseModel):
    user: UserPublic


class UserRoleUpdate(BaseModel):
    role: UserRole


class ProjectCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    due_date: date | None = None


class MemberInvite(BaseModel):
    email: EmailStr
    role: MembershipRole = MembershipRole.member

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower().strip()


class MemberRoleUpdate(BaseModel):
    role: MembershipRole


class ProjectMembershipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: MembershipRole
    user: UserPublic


class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    priority: TaskPriority = TaskPriority.medium
    due_date: date | None = None
    assigned_to_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None
    assigned_to_id: int | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None
    created_at: datetime
    updated_at: datetime
    assigned_to: UserPublic | None
    created_by: UserPublic


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    description: str
    created_at: datetime
    actor: UserPublic
    project_id: int | None
    task_id: int | None


class ProjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    due_date: date | None
    created_at: datetime
    current_role: MembershipRole
    owner: UserPublic
    member_count: int
    task_counts: dict[str, int]
    permissions: PermissionSet


class ProjectDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    due_date: date | None
    created_at: datetime
    current_role: MembershipRole
    owner: UserPublic
    members: list[ProjectMembershipOut]
    tasks: list[TaskOut]
    permissions: PermissionSet


class DashboardStats(BaseModel):
    total_assigned: int
    todo: int
    in_progress: int
    done: int
    overdue: int
    projects: int


class DashboardOverview(BaseModel):
    stats: DashboardStats
    assigned_tasks: list[TaskOut]
    overdue_tasks: list[TaskOut]
    recent_tasks: list[TaskOut]
    upcoming_deadlines: list[TaskOut]
    recent_activity: list[ActivityOut]


class ChartPoint(BaseModel):
    label: str
    value: int


class TeamWorkloadPoint(BaseModel):
    label: str
    todo: int
    in_progress: int
    done: int
    total: int


class ProjectProgressPoint(BaseModel):
    label: str
    todo: int
    in_progress: int
    done: int
    total: int
    completion_rate: int


class AnalyticsOverview(BaseModel):
    completed_tasks_per_week: list[ChartPoint]
    productivity: list[ChartPoint]
    overdue_tasks: list[ChartPoint]
    team_workload: list[TeamWorkloadPoint]
    project_progress: list[ProjectProgressPoint]

import { Suspense, lazy, useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import toast, { Toaster } from "react-hot-toast";
import {
  BarChart3,
  ChevronDown,
  LoaderCircle,
  LogOut,
  Menu,
  Plus,
  ShieldCheck,
  Trash2,
  UserPlus,
} from "lucide-react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";

import ActivityTimeline from "./components/ActivityTimeline";
import { DesktopSidebar, MobileSidebar } from "./components/Sidebar";
import { api } from "./lib/api";

const AnalyticsGrid = lazy(() => import("./components/AnalyticsGrid"));
const DashboardCharts = lazy(() => import("./components/DashboardCharts"));
const KanbanBoard = lazy(() => import("./components/KanbanBoard"));

const routeTitles = {
  "/": "Dashboard",
  "/projects": "Projects",
  "/tasks": "Tasks",
  "/members": "Members",
  "/analytics": "Analytics",
  "/settings": "Settings",
};

function formatDate(value) {
  if (!value) {
    return "No due date";
  }
  return new Date(`${value}T00:00:00`).toLocaleDateString();
}

function isOverdue(task) {
  return Boolean(task?.due_date && task.status !== "done" && new Date(`${task.due_date}T00:00:00`) < new Date());
}

function classForRole(role) {
  return role === "manager" || role === "admin" ? "positive" : "neutral";
}

function useWorkspaceData() {
  const [user, setUser] = useState(null);
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  const [currentProject, setCurrentProject] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [activities, setActivities] = useState([]);
  const [systemUsers, setSystemUsers] = useState([]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [booting, setBooting] = useState(true);
  const [loading, setLoading] = useState({
    workspace: false,
    project: false,
    activities: false,
  });

  const setLoadingFlag = useCallback((key, value) => {
    setLoading((prev) => ({ ...prev, [key]: value }));
  }, []);

  const loadProjectDetail = useCallback(async (projectId) => {
    if (!projectId) {
      setCurrentProject(null);
      return null;
    }
    setLoadingFlag("project", true);
    try {
      const detail = await api(`/api/projects/${projectId}`);
      setCurrentProject(detail);
      return detail;
    } finally {
      setLoadingFlag("project", false);
    }
  }, [setLoadingFlag]);

  const loadActivities = useCallback(async () => {
    setLoadingFlag("activities", true);
    try {
      const data = await api("/api/activity?limit=24");
      setActivities(data);
      return data;
    } finally {
      setLoadingFlag("activities", false);
    }
  }, [setLoadingFlag]);

  const loadWorkspaceForUser = useCallback(
    async (activeUser, preferredProjectId = null) => {
      if (!activeUser) {
        return;
      }
      setLoadingFlag("workspace", true);
      try {
        const requests = [
          api("/api/dashboard"),
          api("/api/projects"),
          api("/api/dashboard/analytics"),
          api("/api/activity?limit=24"),
          activeUser.role === "manager" ? api("/api/users") : Promise.resolve([]),
        ];

        const [dashboardData, projectData, analyticsData, activityData, usersData] = await Promise.all(requests);
        setDashboard(dashboardData);
        setProjects(projectData);
        setAnalytics(analyticsData);
        setActivities(activityData);
        setSystemUsers(usersData);

        const numericPreferredId = Number(preferredProjectId);
        const resolvedProjectId = projectData.some((project) => project.id === numericPreferredId)
          ? numericPreferredId
          : projectData[0]?.id ?? null;

        setSelectedProjectId(resolvedProjectId);
        if (resolvedProjectId) {
          await loadProjectDetail(resolvedProjectId);
        } else {
          setCurrentProject(null);
        }
      } finally {
        setLoadingFlag("workspace", false);
      }
    },
    [loadProjectDetail, setLoadingFlag],
  );

  const refreshWorkspace = useCallback(
    async (preferredProjectId = selectedProjectId) => {
      if (!user) {
        return;
      }
      await loadWorkspaceForUser(user, preferredProjectId);
    },
    [loadWorkspaceForUser, selectedProjectId, user],
  );

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const data = await api("/api/auth/me");
        if (cancelled) {
          return;
        }
        setUser(data.user);
        await loadWorkspaceForUser(data.user);
      } catch {
        if (!cancelled) {
          setUser(null);
        }
      } finally {
        if (!cancelled) {
          setBooting(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [loadWorkspaceForUser]);

  useEffect(() => {
    if (!user) {
      return undefined;
    }
    const intervalId = window.setInterval(() => {
      loadActivities().catch(() => undefined);
    }, 15000);
    return () => window.clearInterval(intervalId);
  }, [loadActivities, user]);

  useEffect(() => {
    if (!user) {
      return;
    }
    if (!selectedProjectId) {
      setCurrentProject(null);
      return;
    }
    if (currentProject?.id === selectedProjectId) {
      return;
    }
    loadProjectDetail(selectedProjectId).catch(() => undefined);
  }, [currentProject?.id, loadProjectDetail, selectedProjectId, user]);

  const login = useCallback(async ({ email, password, expected_role }) => {
    const data = await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password, expected_role }),
    });
    setUser(data.user);
    await loadWorkspaceForUser(data.user);
    toast.success("Login success");
  }, [loadWorkspaceForUser]);

  const signup = useCallback(async ({ full_name, email, password, role }) => {
    const data = await api("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify({ full_name, email, password, role }),
    });
    setUser(data.user);
    await loadWorkspaceForUser(data.user);
    toast.success("Account created");
  }, [loadWorkspaceForUser]);

  const logout = useCallback(async () => {
    await api("/api/auth/logout", { method: "POST" });
    setUser(null);
    setProjects([]);
    setCurrentProject(null);
    setSelectedProjectId(null);
    setDashboard(null);
    setAnalytics(null);
    setActivities([]);
    setSystemUsers([]);
    toast.success("Logged out");
  }, []);

  const createProject = useCallback(async (payload) => {
    const project = await api("/api/projects", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    toast.success("Project created");
    await refreshWorkspace(project.id);
  }, [refreshWorkspace]);

  const deleteProject = useCallback(async (projectId) => {
    try {
      await api(`/api/projects/${projectId}`, { method: "DELETE" });
      toast.success("Project deleted");
      await refreshWorkspace();
    } catch (error) {
      toast.error(error.message);
    }
  }, [refreshWorkspace]);

  const addMember = useCallback(async (payload) => {
    await api(`/api/projects/${selectedProjectId}/members`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    toast.success("Member added");
    await refreshWorkspace(selectedProjectId);
  }, [refreshWorkspace, selectedProjectId]);

  const updateMemberRole = useCallback(async (userId, role) => {
    try {
      await api(`/api/projects/${selectedProjectId}/members/${userId}`, {
        method: "PATCH",
        body: JSON.stringify({ role }),
      });
      toast.success("Member role updated");
      await refreshWorkspace(selectedProjectId);
    } catch (error) {
      toast.error(error.message);
    }
  }, [refreshWorkspace, selectedProjectId]);

  const removeMember = useCallback(async (userId) => {
    try {
      await api(`/api/projects/${selectedProjectId}/members/${userId}`, { method: "DELETE" });
      toast.success("Member removed");
      await refreshWorkspace(selectedProjectId);
    } catch (error) {
      toast.error(error.message);
    }
  }, [refreshWorkspace, selectedProjectId]);

  const createTask = useCallback(async (payload) => {
    await api(`/api/projects/${selectedProjectId}/tasks`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    toast.success("Task created");
    await refreshWorkspace(selectedProjectId);
  }, [refreshWorkspace, selectedProjectId]);

  const updateTask = useCallback(async (taskId, payload, { optimistic = false } = {}) => {
    const snapshot = currentProject ? JSON.parse(JSON.stringify(currentProject)) : null;

    if (optimistic && snapshot) {
      setCurrentProject((prev) => ({
        ...prev,
        tasks: prev.tasks.map((task) => (task.id === taskId ? { ...task, ...payload } : task)),
      }));
    }

    try {
      await api(`/api/projects/${selectedProjectId}/tasks/${taskId}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      toast.success("Task updated");
      await refreshWorkspace(selectedProjectId);
    } catch (error) {
      if (snapshot) {
        setCurrentProject(snapshot);
      }
      toast.error(error.message);
    }
  }, [currentProject, refreshWorkspace, selectedProjectId]);

  const deleteTask = useCallback(async (taskId) => {
    try {
      await api(`/api/projects/${selectedProjectId}/tasks/${taskId}`, { method: "DELETE" });
      toast.success("Task removed");
      await refreshWorkspace(selectedProjectId);
    } catch (error) {
      toast.error(error.message);
    }
  }, [refreshWorkspace, selectedProjectId]);

  const updateSystemRole = useCallback(async (userId, role) => {
    try {
      await api(`/api/users/${userId}/role`, {
        method: "PATCH",
        body: JSON.stringify({ role }),
      });
      toast.success("System role updated");
      await refreshWorkspace(selectedProjectId);
    } catch (error) {
      toast.error(error.message);
    }
  }, [refreshWorkspace, selectedProjectId]);

  return {
    activities,
    addMember,
    analytics,
    booting,
    createProject,
    createTask,
    currentProject,
    dashboard,
    deleteProject,
    deleteTask,
    loadProjectDetail,
    loading,
    login,
    logout,
    mobileSidebarOpen,
    projects,
    refreshWorkspace,
    removeMember,
    selectedProjectId,
    setMobileSidebarOpen,
    setSelectedProjectId,
    setSidebarCollapsed,
    sidebarCollapsed,
    signup,
    systemUsers,
    updateMemberRole,
    updateSystemRole,
    updateTask,
    user,
  };
}

function PageShell({ title, eyebrow, actions, children }) {
  return (
    <motion.section
      animate={{ opacity: 1, y: 0 }}
      className="page-panel"
      initial={{ opacity: 0, y: 18 }}
      transition={{ duration: 0.28, ease: "easeOut" }}
    >
      <div className="page-header">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2>{title}</h2>
        </div>
        <div className="page-actions">{actions}</div>
      </div>
      {children}
    </motion.section>
  );
}

function SectionCard({ title, eyebrow, actions, children, className = "" }) {
  return (
    <motion.article className={`surface-card ${className}`} whileHover={{ y: -2 }}>
      <div className="section-head">
        <div>
          {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
          <h3>{title}</h3>
        </div>
        {actions}
      </div>
      {children}
    </motion.article>
  );
}

function SkeletonGrid() {
  return (
    <div className="skeleton-grid">
      {Array.from({ length: 6 }).map((_, index) => (
        <div className="skeleton-card shimmer" key={index} />
      ))}
    </div>
  );
}

function Modal({ open, onClose, title, children }) {
  return (
    <AnimatePresence>
      {open ? (
        <>
          <motion.button
            animate={{ opacity: 1 }}
            className="modal-backdrop"
            exit={{ opacity: 0 }}
            initial={{ opacity: 0 }}
            onClick={onClose}
            type="button"
          />
          <motion.div
            animate={{ opacity: 1, y: 0, scale: 1 }}
            className="modal-shell"
            exit={{ opacity: 0, y: 20, scale: 0.98 }}
            initial={{ opacity: 0, y: 28, scale: 0.98 }}
          >
            <div className="section-head modal-head">
              <h3>{title}</h3>
              <button className="text-button" onClick={onClose} type="button">
                Close
              </button>
            </div>
            {children}
          </motion.div>
        </>
      ) : null}
    </AnimatePresence>
  );
}

function ProjectPicker({ projects, selectedProjectId, onChange }) {
  return (
    <label className="select-wrap">
      <span>Project</span>
      <div className="select-control">
        <select onChange={(event) => onChange(Number(event.target.value))} value={selectedProjectId || ""}>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
        <ChevronDown size={16} />
      </div>
    </label>
  );
}

function TaskList({ tasks, emptyMessage }) {
  if (!tasks?.length) {
    return <div className="empty-panel">{emptyMessage}</div>;
  }
  return (
    <div className="task-list">
      {tasks.map((task) => (
        <article className={`mini-task ${isOverdue(task) ? "danger-border" : ""}`} key={task.id}>
          <div className="mini-task-row">
            <h4>{task.title}</h4>
            <span className={`status-pill ${task.status}`}>{task.status.replace("_", " ")}</span>
          </div>
          <p>{task.assigned_to?.full_name || "Unassigned"}</p>
          <div className="inline-tags">
            <span className={`priority-pill ${task.priority}`}>{task.priority}</span>
            <span className={isOverdue(task) ? "text-danger" : "text-muted"}>{formatDate(task.due_date)}</span>
          </div>
        </article>
      ))}
    </div>
  );
}

function StatsCards({ stats, isManager }) {
  const items = [
    [isManager ? "Total tasks" : "Assigned", stats.total_assigned, "info"],
    ["To do", stats.todo, "todo"],
    ["In progress", stats.in_progress, "progress"],
    ["Done", stats.done, "done"],
    ["Overdue", stats.overdue, "overdue"],
    ["Projects", stats.projects, "info"],
  ];

  return (
    <div className="stats-grid">
      {items.map(([label, value, tone]) => (
        <motion.article className="stat-card surface-card" key={label} whileHover={{ y: -3 }}>
          <div className={`status-dot ${tone}`} />
          <p className="stat-value">{value}</p>
          <p className="stat-label">{label}</p>
        </motion.article>
      ))}
    </div>
  );
}

function AuthView({ onLogin, onSignup, loading }) {
  const [mode, setMode] = useState("login");
  const [role, setRole] = useState("manager");

  const handleSubmit = async (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload = Object.fromEntries(formData.entries());
    try {
      if (mode === "login") {
        await onLogin({
          email: payload.email,
          password: payload.password,
          expected_role: role,
        });
      } else {
        await onSignup({
          full_name: payload.full_name,
          email: payload.email,
          password: payload.password,
          role,
        });
      }
    } catch (error) {
      toast.error(error.message);
    }
  };

  return (
    <div className="auth-layout">
      <div className="auth-glow" />
      <motion.section animate={{ opacity: 1, y: 0 }} className="auth-card-shell" initial={{ opacity: 0, y: 20 }}>
        <div className="auth-copy">
          <p className="eyebrow">Welcome</p>
          <h1>S and Groups</h1>
          <p>Sign in or create an account to continue.</p>
        </div>

        <div className="auth-toggle-row">
          <div className="segment">
            <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")} type="button">
              Login
            </button>
            <button className={mode === "signup" ? "active" : ""} onClick={() => setMode("signup")} type="button">
              Signup
            </button>
          </div>
          <div className="segment">
            <button className={role === "manager" ? "active" : ""} onClick={() => setRole("manager")} type="button">
              Manager
            </button>
            <button className={role === "employee" ? "active" : ""} onClick={() => setRole("employee")} type="button">
              Member
            </button>
          </div>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {mode === "signup" ? (
            <label>
              <span>Full name</span>
              <input name="full_name" minLength={2} required type="text" />
            </label>
          ) : null}
          <label>
            <span>Email</span>
            <input name="email" required type="email" />
          </label>
          <label>
            <span>Password</span>
            <input name="password" minLength={8} required type="password" />
          </label>
          <button className="primary-button" disabled={loading} type="submit">
            {loading ? "Please wait..." : mode === "login" ? `Login as ${role}` : `Create ${role} account`}
          </button>
        </form>
      </motion.section>
    </div>
  );
}

function DashboardPage({ data }) {
  if (data.loading.workspace || !data.dashboard) {
    return <SkeletonGrid />;
  }

  return (
    <div className="page-stack">
      <PageShell eyebrow="Executive Summary" title="Live team overview">
        <StatsCards isManager={data.user?.role === "manager"} stats={data.dashboard.stats} />
      </PageShell>

      <div className="dashboard-grid">
        <SectionCard title="Recent activity" eyebrow="Timeline">
          <ActivityTimeline activities={data.dashboard.recent_activity} emptyMessage="No recent team activity." />
        </SectionCard>

        <SectionCard title="Upcoming deadlines" eyebrow="Plan ahead">
          <TaskList emptyMessage="No upcoming deadlines." tasks={data.dashboard.upcoming_deadlines} />
        </SectionCard>

        <SectionCard title="Recent tasks" eyebrow="Momentum">
          <TaskList emptyMessage="No recent task changes." tasks={data.dashboard.recent_tasks} />
        </SectionCard>

        <Suspense fallback={<SkeletonGrid />}>
          <DashboardCharts analytics={data.analytics} />
        </Suspense>
      </div>
    </div>
  );
}

function ProjectsPage({ data }) {
  const [projectModalOpen, setProjectModalOpen] = useState(false);
  const permissions = data.user?.role === "manager";

  const handleCreateProject = async (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    try {
      await data.createProject(Object.fromEntries(formData.entries()));
      setProjectModalOpen(false);
      event.currentTarget.reset();
    } catch (error) {
      toast.error(error.message);
    }
  };

  return (
    <div className="page-stack">
      <PageShell
        actions={
          permissions ? (
            <button className="primary-button" onClick={() => setProjectModalOpen(true)} type="button">
              <Plus size={16} />
              Create project
            </button>
          ) : null
        }
        eyebrow="Portfolio"
        title="Projects workspace"
      >
        {data.loading.workspace ? (
          <SkeletonGrid />
        ) : (
          <div className="project-grid">
            <div className="project-list">
              {data.projects.map((project) => (
                <motion.button
                  className={`project-tile ${data.selectedProjectId === project.id ? "active" : ""}`}
                  key={project.id}
                  onClick={() => data.setSelectedProjectId(project.id)}
                  type="button"
                  whileHover={{ y: -2 }}
                >
                  <div className="project-tile-row">
                    <div>
                      <h3>{project.name}</h3>
                      <p>{project.description || "No description yet."}</p>
                    </div>
                    <span className={`role-pill ${classForRole(project.current_role)}`}>{project.current_role}</span>
                  </div>
                  <div className="progress-row">
                    <span>Done {project.task_counts.done}</span>
                    <span>In progress {project.task_counts.in_progress}</span>
                    <span>To do {project.task_counts.todo}</span>
                  </div>
                  <div className="progress-track">
                    <span
                      className="progress-fill"
                      style={{
                        width: `${Math.min(
                          100,
                          ((project.task_counts.done || 0) /
                            Math.max(1, project.task_counts.done + project.task_counts.todo + project.task_counts.in_progress)) *
                            100,
                        )}%`,
                      }}
                    />
                  </div>
                </motion.button>
              ))}
            </div>

            <SectionCard
              actions={
                permissions && data.currentProject ? (
                  <button className="text-button danger" onClick={() => data.deleteProject(data.currentProject.id)} type="button">
                    <Trash2 size={16} />
                    Delete project
                  </button>
                ) : null
              }
              eyebrow="Selected Project"
              title={data.currentProject?.name || "Pick a project"}
            >
              {data.loading.project ? (
                <div className="skeleton-card shimmer tall" />
              ) : data.currentProject ? (
                <div className="detail-stack">
                  <p className="lead-copy">{data.currentProject.description || "No description provided."}</p>
                  <div className="detail-metrics">
                    <div>
                      <span className="metric-label">Due date</span>
                      <strong>{formatDate(data.currentProject.due_date)}</strong>
                    </div>
                    <div>
                      <span className="metric-label">Members</span>
                      <strong>{data.currentProject.members.length}</strong>
                    </div>
                    <div>
                      <span className="metric-label">Visible tasks</span>
                      <strong>{data.currentProject.tasks.length}</strong>
                    </div>
                  </div>
                  <ActivityTimeline
                    activities={data.activities.filter((item) => item.project_id === data.currentProject.id).slice(0, 6)}
                    emptyMessage="No project activity yet."
                  />
                </div>
              ) : (
                <div className="empty-panel">Choose a project to inspect delivery health and activity.</div>
              )}
            </SectionCard>
          </div>
        )}
      </PageShell>

      <Modal onClose={() => setProjectModalOpen(false)} open={projectModalOpen} title="Create project">
        <form className="modal-form" onSubmit={handleCreateProject}>
          <label>
            <span>Project name</span>
            <input minLength={3} name="name" required type="text" />
          </label>
          <label>
            <span>Description</span>
            <textarea name="description" rows={4} />
          </label>
          <label>
            <span>Due date</span>
            <input name="due_date" type="date" />
          </label>
          <button className="primary-button" type="submit">Create project</button>
        </form>
      </Modal>
    </div>
  );
}

function TasksPage({ data }) {
  const [taskModalOpen, setTaskModalOpen] = useState(false);
  const canManageTasks = data.user?.role === "manager";

  const handleCreateTask = async (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload = Object.fromEntries(formData.entries());
    payload.assigned_to_id = payload.assigned_to_id ? Number(payload.assigned_to_id) : null;
    try {
      await data.createTask(payload);
      setTaskModalOpen(false);
      event.currentTarget.reset();
    } catch (error) {
      toast.error(error.message);
    }
  };

  return (
    <div className="page-stack">
      <PageShell
        actions={
          <div className="inline-actions">
            {data.projects.length ? (
              <ProjectPicker
                onChange={data.setSelectedProjectId}
                projects={data.projects}
                selectedProjectId={data.selectedProjectId}
              />
            ) : null}
            {canManageTasks && data.currentProject ? (
              <button className="primary-button" onClick={() => setTaskModalOpen(true)} type="button">
                <Plus size={16} />
                Create task
              </button>
            ) : null}
          </div>
        }
        eyebrow="Delivery board"
        title="Drag-and-drop Kanban"
      >
        {data.loading.project ? (
          <SkeletonGrid />
        ) : data.currentProject ? (
          <Suspense fallback={<div className="skeleton-card shimmer tall" />}>
            <KanbanBoard
              canManageTasks={canManageTasks}
              currentUser={data.user}
              onDeleteTask={data.deleteTask}
              onTaskMove={(taskId, nextStatus) => data.updateTask(taskId, { status: nextStatus }, { optimistic: true })}
              tasks={data.currentProject.tasks}
            />
          </Suspense>
        ) : (
          <div className="empty-panel">Create or select a project to view the Kanban board.</div>
        )}
      </PageShell>

      <Modal onClose={() => setTaskModalOpen(false)} open={taskModalOpen} title="Create task">
        <form className="modal-form" onSubmit={handleCreateTask}>
          <label>
            <span>Title</span>
            <input minLength={3} name="title" required type="text" />
          </label>
          <label>
            <span>Description</span>
            <textarea name="description" rows={4} />
          </label>
          <label>
            <span>Assignee</span>
            <select name="assigned_to_id">
              <option value="">Unassigned</option>
              {data.currentProject?.members.map((member) => (
                <option key={member.user.id} value={member.user.id}>
                  {member.user.full_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Priority</span>
            <select defaultValue="medium" name="priority">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </label>
          <label>
            <span>Due date</span>
            <input name="due_date" type="date" />
          </label>
          <button className="primary-button" type="submit">Create task</button>
        </form>
      </Modal>
    </div>
  );
}

function MembersPage({ data }) {
  const [memberModalOpen, setMemberModalOpen] = useState(false);
  const canManageMembers = data.user?.role === "manager";

  const handleAddMember = async (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    try {
      await data.addMember(Object.fromEntries(formData.entries()));
      setMemberModalOpen(false);
      event.currentTarget.reset();
    } catch (error) {
      toast.error(error.message);
    }
  };

  return (
    <div className="page-stack">
      <PageShell
        actions={
          <div className="inline-actions">
            {data.projects.length ? (
              <ProjectPicker
                onChange={data.setSelectedProjectId}
                projects={data.projects}
                selectedProjectId={data.selectedProjectId}
              />
            ) : null}
            {canManageMembers && data.currentProject ? (
              <button className="primary-button" onClick={() => setMemberModalOpen(true)} type="button">
                <UserPlus size={16} />
                Add member
              </button>
            ) : null}
          </div>
        }
        eyebrow="Access control"
        title="Team members and roles"
      >
        {data.loading.project ? (
          <SkeletonGrid />
        ) : data.currentProject ? (
          <div className="member-grid">
            <SectionCard title="Project roster" eyebrow="Team">
              <div className="member-list">
                {data.currentProject.members.map((member) => (
                  <article className="member-card" key={member.user.id}>
                    <div className="member-card-top">
                      <div className="avatar">{member.user.full_name.slice(0, 2).toUpperCase()}</div>
                      <div>
                        <h4>{member.user.full_name}</h4>
                        <p>{member.user.email}</p>
                      </div>
                    </div>
                    <div className="member-card-actions">
                      <span className={`role-pill ${classForRole(member.role)}`}>{member.role}</span>
                      {canManageMembers && data.currentProject.owner.id !== member.user.id ? (
                        <>
                          <select
                            className="mini-select"
                            onChange={(event) => data.updateMemberRole(member.user.id, event.target.value)}
                            value={member.role}
                          >
                            <option value="member">Member</option>
                            <option value="admin">Admin</option>
                          </select>
                          <button className="text-button danger" onClick={() => data.removeMember(member.user.id)} type="button">
                            Remove
                          </button>
                        </>
                      ) : null}
                    </div>
                  </article>
                ))}
              </div>
            </SectionCard>

            <SectionCard title="Recent access activity" eyebrow="Audit trail">
              <ActivityTimeline
                activities={data.activities.filter((item) => item.project_id === data.currentProject.id).slice(0, 8)}
                emptyMessage="No membership activity yet."
              />
            </SectionCard>
          </div>
        ) : (
          <div className="empty-panel">Select a project to review members and recent changes.</div>
        )}
      </PageShell>

      <Modal onClose={() => setMemberModalOpen(false)} open={memberModalOpen} title="Add member">
        <form className="modal-form" onSubmit={handleAddMember}>
          <label>
            <span>User email</span>
            <input name="email" required type="email" />
          </label>
          <label>
            <span>Role</span>
            <select defaultValue="member" name="role">
              <option value="member">Member</option>
              <option value="admin">Admin</option>
            </select>
          </label>
          <button className="primary-button" type="submit">Add member</button>
        </form>
      </Modal>
    </div>
  );
}

function AnalyticsPage({ data }) {
  return (
    <div className="page-stack">
      <PageShell eyebrow="Insights" title="Analytics cockpit">
        {data.loading.workspace || !data.analytics ? (
          <SkeletonGrid />
        ) : (
          <Suspense fallback={<SkeletonGrid />}>
            <AnalyticsGrid analytics={data.analytics} />
          </Suspense>
        )}
      </PageShell>
    </div>
  );
}

function SettingsPage({ data }) {
  return (
    <div className="page-stack">
      <PageShell eyebrow="System controls" title="Settings and role management">
        <div className="settings-grid">
          <SectionCard title="Profile and permissions" eyebrow="Current user">
            <div className="profile-block">
              <div className="avatar large">{data.user.full_name.slice(0, 2).toUpperCase()}</div>
              <div>
                <h3>{data.user.full_name}</h3>
                <p>{data.user.email}</p>
                <div className="inline-tags">
                  <span className={`role-pill ${classForRole(data.user.role)}`}>{data.user.role}</span>
                  <span className="role-pill info">
                    <ShieldCheck size={14} />
                    {data.user.role === "manager" ? "Full workspace control" : "Assigned-task access"}
                  </span>
                </div>
              </div>
            </div>
          </SectionCard>

          <SectionCard title="Workspace users" eyebrow="RBAC">
            {data.user.role !== "manager" ? (
              <div className="empty-panel">Manager-only controls are hidden for member accounts.</div>
            ) : (
              <div className="member-list">
                {data.systemUsers.map((workspaceUser) => (
                  <article className="member-card" key={workspaceUser.id}>
                    <div className="member-card-top">
                      <div className="avatar">{workspaceUser.full_name.slice(0, 2).toUpperCase()}</div>
                      <div>
                        <h4>{workspaceUser.full_name}</h4>
                        <p>{workspaceUser.email}</p>
                      </div>
                    </div>
                    <div className="member-card-actions">
                      <select
                        className="mini-select"
                        onChange={(event) => data.updateSystemRole(workspaceUser.id, event.target.value)}
                        value={workspaceUser.role}
                      >
                        <option value="employee">Employee</option>
                        <option value="manager">Manager</option>
                      </select>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </SectionCard>

        </div>
      </PageShell>
    </div>
  );
}

function WorkspaceLayout({ data }) {
  const location = useLocation();
  const navigate = useNavigate();
  const pageTitle = routeTitles[location.pathname] || "Dashboard";
  const closeMobileSidebar = data.setMobileSidebarOpen;

  useEffect(() => {
    closeMobileSidebar(false);
  }, [closeMobileSidebar, location.pathname]);

  return (
    <div className="app-frame">
      <DesktopSidebar collapsed={data.sidebarCollapsed} setCollapsed={data.setSidebarCollapsed} />
      <MobileSidebar onClose={() => data.setMobileSidebarOpen(false)} open={data.mobileSidebarOpen} />

      <div className="main-shell">
        <header className="topbar">
          <div className="topbar-left">
            <button className="icon-button mobile-only" onClick={() => data.setMobileSidebarOpen(true)} type="button">
              <Menu size={18} />
            </button>
            <div>
              <p className="eyebrow">S and Groups</p>
              <h1>{pageTitle}</h1>
            </div>
          </div>
          <div className="topbar-right">
            <button className="ghost-button" onClick={() => navigate("/analytics")} type="button">
              <BarChart3 size={16} />
              Analytics
            </button>
            <div className="user-chip">
              <div className="avatar small">{data.user.full_name.slice(0, 2).toUpperCase()}</div>
              <div>
                <strong>{data.user.full_name}</strong>
                <span>{data.user.role}</span>
              </div>
            </div>
            <button className="icon-button" onClick={data.logout} type="button">
              <LogOut size={18} />
            </button>
          </div>
        </header>

        <main className="content-shell">
          <AnimatePresence mode="wait">
            <motion.div
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 12 }}
              initial={{ opacity: 0, y: 12 }}
              key={location.pathname}
              transition={{ duration: 0.22 }}
            >
              <Routes>
                <Route element={<DashboardPage data={data} />} path="/" />
                <Route element={<ProjectsPage data={data} />} path="/projects" />
                <Route element={<TasksPage data={data} />} path="/tasks" />
                <Route element={<MembersPage data={data} />} path="/members" />
                <Route element={<AnalyticsPage data={data} />} path="/analytics" />
                <Route element={<SettingsPage data={data} />} path="/settings" />
                <Route element={<Navigate replace to="/" />} path="*" />
              </Routes>
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  const data = useWorkspaceData();

  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          className: "toast-dark",
          duration: 2800,
          style: {
            background: "#151922",
            color: "#F3F4F6",
            border: "1px solid #262B36",
            boxShadow: "0 18px 40px rgba(0,0,0,0.35)",
          },
        }}
      />
      {data.booting ? (
        <div className="boot-splash">
          <LoaderCircle className="spin" size={28} />
          <span>Loading workspace...</span>
        </div>
      ) : data.user ? (
        <WorkspaceLayout data={data} />
      ) : (
        <AuthView loading={data.loading.workspace} onLogin={data.login} onSignup={data.signup} />
      )}
    </>
  );
}

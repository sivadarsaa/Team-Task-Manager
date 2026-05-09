import { AnimatePresence, motion } from "framer-motion";
import {
  BarChart3,
  ChevronLeft,
  ChevronRight,
  FolderOpen,
  LayoutDashboard,
  ListTodo,
  Settings,
  Users,
  X,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/projects", label: "Projects", icon: FolderOpen },
  { to: "/tasks", label: "Tasks", icon: ListTodo },
  { to: "/members", label: "Members", icon: Users },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/settings", label: "Settings", icon: Settings },
];

function SidebarContent({ collapsed, onClose }) {
  return (
    <div className={`sidebar-shell ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-brand">
        <div className="sidebar-logo">SG</div>
        {!collapsed && (
          <div>
            <p className="sidebar-eyebrow">Workspace</p>
            <h1>S and Groups</h1>
          </div>
        )}
        {onClose ? (
          <button className="icon-button mobile-only" onClick={onClose} type="button" aria-label="Close menu">
            <X size={18} />
          </button>
        ) : null}
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              end={item.to === "/"}
              key={item.to}
              to={item.to}
              className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`}
            >
              <Icon size={18} />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
}

export function DesktopSidebar({ collapsed, setCollapsed }) {
  return (
    <motion.aside
      animate={{ width: collapsed ? 92 : 280 }}
      className="sidebar desktop-sidebar"
      transition={{ duration: 0.28, ease: "easeInOut" }}
    >
      <SidebarContent collapsed={collapsed} />
      <button className="collapse-button" onClick={() => setCollapsed((value) => !value)} type="button">
        {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
      </button>
    </motion.aside>
  );
}

export function MobileSidebar({ open, onClose }) {
  return (
    <AnimatePresence>
      {open ? (
        <>
          <motion.button
            animate={{ opacity: 1 }}
            className="drawer-backdrop"
            exit={{ opacity: 0 }}
            initial={{ opacity: 0 }}
            onClick={onClose}
            type="button"
          />
          <motion.aside
            animate={{ x: 0 }}
            className="sidebar mobile-sidebar"
            exit={{ x: "-100%" }}
            initial={{ x: "-100%" }}
            transition={{ duration: 0.24, ease: "easeOut" }}
          >
            <SidebarContent collapsed={false} onClose={onClose} />
          </motion.aside>
        </>
      ) : null}
    </AnimatePresence>
  );
}

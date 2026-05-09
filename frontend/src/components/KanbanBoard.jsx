import { useMemo, useState } from "react";
import { DndContext, DragOverlay, PointerSensor, useDraggable, useDroppable, useSensor, useSensors } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { motion } from "framer-motion";
import { CalendarClock, CircleAlert, CircleCheck, LoaderCircle, UserRound } from "lucide-react";

const columns = [
  { id: "todo", label: "TODO", icon: CircleAlert },
  { id: "in_progress", label: "IN PROGRESS", icon: LoaderCircle },
  { id: "done", label: "DONE", icon: CircleCheck },
];

function formatDate(value) {
  if (!value) {
    return "No due date";
  }
  return new Date(`${value}T00:00:00`).toLocaleDateString();
}

function TaskCard({ task, canDrag, onDelete }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `task-${task.id}`,
    data: { type: "task", task },
    disabled: !canDrag,
  });

  return (
    <motion.article
      className={`task-card priority-${task.priority} ${isDragging ? "dragging" : ""}`}
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform) }}
      whileHover={{ y: -2, boxShadow: "0 20px 34px rgba(0, 0, 0, 0.35)" }}
      {...listeners}
      {...attributes}
    >
      <div className="task-card-row">
        <span className={`priority-pill ${task.priority}`}>{task.priority}</span>
        <span className={`status-pill ${task.status}`}>{task.status.replace("_", " ")}</span>
      </div>
      <h4>{task.title}</h4>
      <p>{task.description || "No description provided."}</p>
      <div className="task-card-meta">
        <span>
          <UserRound size={14} />
          {task.assigned_to?.full_name || "Unassigned"}
        </span>
        <span>
          <CalendarClock size={14} />
          {formatDate(task.due_date)}
        </span>
      </div>
      {onDelete ? (
        <button className="text-button danger" onClick={() => onDelete(task.id)} type="button">
          Delete
        </button>
      ) : null}
    </motion.article>
  );
}

function KanbanColumn({ column, tasks, count, children }) {
  const { setNodeRef, isOver } = useDroppable({
    id: column.id,
    data: { type: "column", status: column.id },
  });
  const Icon = column.icon;

  return (
    <section className={`kanban-column ${isOver ? "over" : ""}`} ref={setNodeRef}>
      <div className="kanban-column-header">
        <div className="kanban-column-title">
          <Icon size={16} />
          <span>{column.label}</span>
        </div>
        <span className="count-chip">{count}</span>
      </div>
      <div className="kanban-column-body">
        {tasks.map((task) => children(task))}
      </div>
    </section>
  );
}

export default function KanbanBoard({ tasks, currentUser, canManageTasks, onTaskMove, onDeleteTask }) {
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }));
  const [activeTask, setActiveTask] = useState(null);

  const grouped = useMemo(
    () =>
      columns.map((column) => ({
        ...column,
        tasks: tasks.filter((task) => task.status === column.id),
      })),
    [tasks],
  );

  const canDragTask = (task) => canManageTasks || task.assigned_to?.id === currentUser?.id;

  return (
    <DndContext
      onDragEnd={({ active, over }) => {
        if (!over) {
          setActiveTask(null);
          return;
        }
        const draggedTask = active.data.current?.task;
        const nextStatus = over.data.current?.status || over.data.current?.task?.status;
        if (draggedTask && nextStatus && draggedTask.status !== nextStatus) {
          onTaskMove(draggedTask.id, nextStatus);
        }
        setActiveTask(null);
      }}
      onDragStart={({ active }) => setActiveTask(active.data.current?.task || null)}
      sensors={sensors}
    >
      <div className="kanban-board">
        {grouped.map((column) => (
          <KanbanColumn column={column} count={column.tasks.length} key={column.id} tasks={column.tasks}>
            {(task) => (
              <TaskCard
                canDrag={canDragTask(task)}
                key={task.id}
                onDelete={canManageTasks ? onDeleteTask : null}
                task={task}
              />
            )}
          </KanbanColumn>
        ))}
      </div>
      <DragOverlay>
        {activeTask ? <TaskCard canDrag currentUser={currentUser} task={activeTask} /> : null}
      </DragOverlay>
    </DndContext>
  );
}

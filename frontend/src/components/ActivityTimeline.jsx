import { motion } from "framer-motion";
import { Activity, Clock3 } from "lucide-react";

function relativeTime(value) {
  const diff = Date.now() - new Date(value).getTime();
  const minutes = Math.max(1, Math.round(diff / 60000));
  if (minutes < 60) {
    return `${minutes}m ago`;
  }
  const hours = Math.round(minutes / 60);
  if (hours < 24) {
    return `${hours}h ago`;
  }
  const days = Math.round(hours / 24);
  return `${days}d ago`;
}

export default function ActivityTimeline({ activities, emptyMessage = "No activity yet." }) {
  if (!activities?.length) {
    return (
      <div className="empty-panel">
        <Activity size={18} />
        <span>{emptyMessage}</span>
      </div>
    );
  }

  return (
    <div className="timeline">
      {activities.map((item, index) => (
        <motion.article
          animate={{ opacity: 1, y: 0 }}
          className="timeline-item"
          initial={{ opacity: 0, y: 14 }}
          key={item.id}
          transition={{ delay: index * 0.04 }}
        >
          <div className="timeline-rail">
            <span className="timeline-dot" />
          </div>
          <div className="timeline-card">
            <div className="timeline-heading">
              <div className="avatar small">{item.actor.full_name.slice(0, 2).toUpperCase()}</div>
              <div>
                <p>{item.description}</p>
                <div className="timeline-meta">
                  <span>{item.action.replace(".", " ")}</span>
                  <span className="inline-meta">
                    <Clock3 size={14} />
                    {relativeTime(item.created_at)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </motion.article>
      ))}
    </div>
  );
}

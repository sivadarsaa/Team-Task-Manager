import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function ChartCard({ title, children }) {
  return (
    <article className="surface-card">
      <div className="section-head">
        <div>
          <h3>{title}</h3>
        </div>
      </div>
      <div className="chart-frame">{children}</div>
    </article>
  );
}

export default function DashboardCharts({ analytics }) {
  return (
    <>
      <ChartCard title="Completed tasks per week">
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={analytics?.completed_tasks_per_week || []}>
            <CartesianGrid stroke="#262B36" vertical={false} />
            <XAxis dataKey="label" stroke="#9CA3AF" tickLine={false} axisLine={false} />
            <YAxis stroke="#9CA3AF" tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ background: "#111318", border: "1px solid #262B36" }} />
            <Bar dataKey="value" radius={[10, 10, 0, 0]} fill="#5E6AD2" />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Team workload overview">
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={analytics?.team_workload || []}>
            <CartesianGrid stroke="#262B36" vertical={false} />
            <XAxis dataKey="label" stroke="#9CA3AF" tickLine={false} axisLine={false} />
            <YAxis stroke="#9CA3AF" tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ background: "#111318", border: "1px solid #262B36" }} />
            <Bar stackId="work" dataKey="todo" fill="#6B7280" radius={[10, 10, 0, 0]} />
            <Bar stackId="work" dataKey="in_progress" fill="#F59E0B" radius={[10, 10, 0, 0]} />
            <Bar stackId="work" dataKey="done" fill="#22C55E" radius={[10, 10, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>
    </>
  );
}

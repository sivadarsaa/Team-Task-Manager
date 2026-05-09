import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const chartPalette = ["#5E6AD2", "#22C55E", "#F59E0B", "#EF4444", "#3B82F6"];

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

export default function AnalyticsGrid({ analytics }) {
  return (
    <div className="analytics-grid">
      <ChartCard title="Completed tasks per week">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={analytics.completed_tasks_per_week}>
            <CartesianGrid stroke="#262B36" vertical={false} />
            <XAxis dataKey="label" stroke="#9CA3AF" tickLine={false} axisLine={false} />
            <YAxis stroke="#9CA3AF" tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ background: "#111318", border: "1px solid #262B36" }} />
            <Bar dataKey="value" radius={[10, 10, 0, 0]} fill="#5E6AD2" />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Productivity chart">
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={analytics.productivity}>
            <defs>
              <linearGradient id="productivityFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="5%" stopColor="#5E6AD2" stopOpacity={0.65} />
                <stop offset="95%" stopColor="#5E6AD2" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#262B36" vertical={false} />
            <XAxis dataKey="label" stroke="#9CA3AF" tickLine={false} axisLine={false} />
            <YAxis stroke="#9CA3AF" tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ background: "#111318", border: "1px solid #262B36" }} />
            <Area dataKey="value" stroke="#5E6AD2" fill="url(#productivityFill)" strokeWidth={3} />
          </AreaChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Overdue tasks chart">
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Tooltip contentStyle={{ background: "#111318", border: "1px solid #262B36" }} />
            <Pie data={analytics.overdue_tasks} dataKey="value" innerRadius={65} outerRadius={96} paddingAngle={3}>
              {analytics.overdue_tasks.map((entry, index) => (
                <Cell fill={chartPalette[index % chartPalette.length]} key={entry.label} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Team workload chart">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={analytics.team_workload}>
            <CartesianGrid stroke="#262B36" vertical={false} />
            <XAxis dataKey="label" stroke="#9CA3AF" tickLine={false} axisLine={false} />
            <YAxis stroke="#9CA3AF" tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ background: "#111318", border: "1px solid #262B36" }} />
            <Bar dataKey="todo" stackId="a" fill="#6B7280" radius={[8, 8, 0, 0]} />
            <Bar dataKey="in_progress" stackId="a" fill="#F59E0B" radius={[8, 8, 0, 0]} />
            <Bar dataKey="done" stackId="a" fill="#22C55E" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Project progress chart">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={analytics.project_progress} layout="vertical">
            <CartesianGrid stroke="#262B36" horizontal={false} />
            <XAxis type="number" stroke="#9CA3AF" tickLine={false} axisLine={false} />
            <YAxis type="category" dataKey="label" stroke="#9CA3AF" tickLine={false} axisLine={false} width={120} />
            <Tooltip contentStyle={{ background: "#111318", border: "1px solid #262B36" }} />
            <Bar dataKey="completion_rate" radius={[0, 10, 10, 0]} fill="#22C55E" />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}

import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  useDealsByStage,
  useLeadsOverTime,
  useSummary,
} from "../api/hooks";

function money(v: number) {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(v);
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="card p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-bold text-slate-800">{value}</div>
    </div>
  );
}

export default function DashboardPage() {
  const summary = useSummary();
  const byStage = useDealsByStage();
  const overTime = useLeadsOverTime(30);

  const s = summary.data;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Kpi label="Total leads" value={s ? String(s.leads_total) : "—"} />
        <Kpi label="Open pipeline" value={s ? money(s.open_pipeline_value) : "—"} />
        <Kpi label="Won value" value={s ? money(s.won_value) : "—"} />
        <Kpi
          label="Win rate"
          value={s ? `${Math.round(s.win_rate * 100)}%` : "—"}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Deals by stage */}
        <div className="card p-4">
          <h2 className="mb-3 text-sm font-semibold text-slate-700">
            Deals by stage (value)
          </h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={byStage.data ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" />
              <XAxis dataKey="stage" fontSize={12} />
              <YAxis fontSize={12} />
              <Tooltip formatter={(v: number) => money(v)} />
              <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Leads over time */}
        <div className="card p-4">
          <h2 className="mb-3 text-sm font-semibold text-slate-700">
            Leads over time (30d)
          </h2>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={overTime.data ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" />
              <XAxis dataKey="day" fontSize={12} />
              <YAxis allowDecimals={false} fontSize={12} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#4f46e5"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

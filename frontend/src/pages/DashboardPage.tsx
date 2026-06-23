import {
  DollarSign,
  TrendingUp,
  Trophy,
  Users,
  type LucideIcon,
} from "lucide-react";
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

import { useDealsByStage, useLeadsOverTime, useSummary } from "../api/hooks";

function money(v: number) {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(v);
}

const ACCENTS: Record<string, string> = {
  blue: "bg-brand-50 text-brand-600",
  green: "bg-emerald-50 text-emerald-600",
  amber: "bg-amber-50 text-amber-600",
  purple: "bg-ai-100/70 text-ai-600",
};

function Kpi({
  label,
  value,
  icon: Icon,
  accent,
  hint,
}: {
  label: string;
  value: string;
  icon: LucideIcon;
  accent: keyof typeof ACCENTS | string;
  hint?: string;
}) {
  return (
    <div className="card card-hover p-5">
      <div className="flex items-start justify-between">
        <span className="text-sm font-medium text-slate-500">{label}</span>
        <span className={`grid h-9 w-9 place-items-center rounded-lg ${ACCENTS[accent]}`}>
          <Icon size={18} />
        </span>
      </div>
      <div className="mt-3 text-3xl font-bold tracking-tight text-slate-900">
        {value}
      </div>
      {hint && (
        <div className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-emerald-600">
          <TrendingUp size={13} /> {hint}
        </div>
      )}
    </div>
  );
}

function ChartCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="card p-5">
      <h2 className="mb-4 text-sm font-semibold text-slate-700">{title}</h2>
      {children}
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
      <div>
        <h1>Dashboard</h1>
        <p className="mt-1 text-sm text-slate-500">
          Track and manage your leads, deals, and sales pipeline.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi
          label="Total leads"
          value={s ? String(s.leads_total) : "—"}
          icon={Users}
          accent="blue"
          hint={s ? `${s.leads_stale} stale` : undefined}
        />
        <Kpi
          label="Open pipeline"
          value={s ? money(s.open_pipeline_value) : "—"}
          icon={TrendingUp}
          accent="purple"
          hint={s ? `${s.open_deals} open deals` : undefined}
        />
        <Kpi
          label="Won value"
          value={s ? money(s.won_value) : "—"}
          icon={DollarSign}
          accent="green"
          hint={s ? `${s.won_deals} won` : undefined}
        />
        <Kpi
          label="Win rate"
          value={s ? `${Math.round(s.win_rate * 100)}%` : "—"}
          icon={Trophy}
          accent="amber"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ChartCard title="Deals by stage (value)">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={byStage.data ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" vertical={false} />
              <XAxis dataKey="stage" fontSize={12} stroke="#94a3b8" tickLine={false} />
              <YAxis fontSize={12} stroke="#94a3b8" tickLine={false} axisLine={false} />
              <Tooltip
                formatter={(v: number) => money(v)}
                contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }}
              />
              <Bar dataKey="value" fill="#2563eb" radius={[6, 6, 0, 0]} maxBarSize={48} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Leads over time (30d)">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={overTime.data ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" vertical={false} />
              <XAxis dataKey="day" fontSize={12} stroke="#94a3b8" tickLine={false} />
              <YAxis
                allowDecimals={false}
                fontSize={12}
                stroke="#94a3b8"
                tickLine={false}
                axisLine={false}
              />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#7c3aed"
                strokeWidth={2.5}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}

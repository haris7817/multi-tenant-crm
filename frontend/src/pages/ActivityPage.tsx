import { useState } from "react";

import { useActivity } from "../api/hooks";
import type { AuditAction, AuditLog } from "../lib/types";

const ACTION_COLORS: Record<AuditAction, string> = {
  created: "bg-green-100 text-green-700",
  updated: "bg-blue-100 text-blue-700",
  deleted: "bg-red-100 text-red-700",
};

function Changes({ changes }: { changes: AuditLog["changes"] }) {
  const keys = Object.keys(changes ?? {});
  if (keys.length === 0) return null;
  return (
    <div className="mt-1 space-y-0.5 text-xs text-slate-500">
      {keys.map((k) => (
        <div key={k}>
          <span className="font-medium text-slate-600">{k}</span>:{" "}
          <span className="text-red-500 line-through">
            {String(changes[k][0] ?? "∅")}
          </span>{" "}
          → <span className="text-green-600">{String(changes[k][1] ?? "∅")}</span>
        </div>
      ))}
    </div>
  );
}

export default function ActivityPage() {
  const [action, setAction] = useState("");
  const { data, isLoading } = useActivity({ action: action || undefined });

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Activity</h1>
        <select
          className="input max-w-[160px]"
          value={action}
          onChange={(e) => setAction(e.target.value)}
        >
          <option value="">All actions</option>
          <option value="created">Created</option>
          <option value="updated">Updated</option>
          <option value="deleted">Deleted</option>
        </select>
      </div>

      <div className="card divide-y divide-slate-100">
        {isLoading && <div className="p-4 text-slate-400">Loading…</div>}
        {data?.results.map((log) => (
          <div key={log.id} className="flex items-start gap-3 p-4">
            <span
              className={`mt-0.5 rounded-full px-2 py-0.5 text-xs font-medium ${ACTION_COLORS[log.action]}`}
            >
              {log.action}
            </span>
            <div className="flex-1">
              <div className="text-sm text-slate-800">
                <span className="font-medium">{log.actor_email ?? "system"}</span>{" "}
                {log.action} {log.target_model}{" "}
                <span className="font-medium">{log.target_repr}</span>
              </div>
              <Changes changes={log.changes} />
            </div>
            <div className="whitespace-nowrap text-xs text-slate-400">
              {new Date(log.created_at).toLocaleString()}
            </div>
          </div>
        ))}
        {data && data.results.length === 0 && (
          <div className="p-4 text-slate-400">No activity yet.</div>
        )}
      </div>
    </div>
  );
}

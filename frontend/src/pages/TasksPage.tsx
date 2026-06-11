import { useState } from "react";

import { useDeleteTask, useTasks, useUpdateTask } from "../api/hooks";
import { useAuth } from "../auth/AuthContext";
import TaskFormModal from "../components/TaskFormModal";
import type { Priority } from "../lib/types";

const PRIORITY_COLORS: Record<Priority, string> = {
  low: "bg-slate-100 text-slate-600",
  medium: "bg-blue-100 text-blue-700",
  high: "bg-red-100 text-red-700",
};

export default function TasksPage() {
  const { hasRole } = useAuth();
  const [done, setDone] = useState("");
  const [priority, setPriority] = useState("");
  const { data, isLoading } = useTasks({
    is_done: done || undefined,
    priority: priority || undefined,
  });
  const update = useUpdateTask();
  const del = useDeleteTask();
  const [showForm, setShowForm] = useState(false);

  const canWrite = hasRole("sales_rep");
  const canDelete = hasRole("manager");

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Tasks</h1>
        {canWrite && (
          <button className="btn-primary" onClick={() => setShowForm(true)}>
            + New task
          </button>
        )}
      </div>

      <div className="mb-4 flex gap-3">
        <select
          className="input max-w-[160px]"
          value={done}
          onChange={(e) => setDone(e.target.value)}
        >
          <option value="">All</option>
          <option value="false">Open</option>
          <option value="true">Done</option>
        </select>
        <select
          className="input max-w-[160px]"
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
        >
          <option value="">Any priority</option>
          {(Object.keys(PRIORITY_COLORS) as Priority[]).map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3"></th>
              <th className="px-4 py-3">Title</th>
              <th className="px-4 py-3">Priority</th>
              <th className="px-4 py-3">Due</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && (
              <tr>
                <td className="px-4 py-6 text-slate-400" colSpan={5}>
                  Loading…
                </td>
              </tr>
            )}
            {data?.results.map((task) => (
              <tr key={task.id} className="hover:bg-slate-50">
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={task.is_done}
                    disabled={!canWrite}
                    onChange={() =>
                      update.mutate({ id: task.id, is_done: !task.is_done })
                    }
                  />
                </td>
                <td
                  className={`px-4 py-3 font-medium ${task.is_done ? "text-slate-400 line-through" : "text-slate-800"}`}
                >
                  {task.title}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${PRIORITY_COLORS[task.priority]}`}
                  >
                    {task.priority}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-500">
                  {task.due_date ?? "—"}
                </td>
                <td className="px-4 py-3 text-right">
                  {canDelete && (
                    <button
                      className="text-red-500 hover:underline"
                      onClick={() => {
                        if (confirm(`Delete task "${task.title}"?`))
                          del.mutate(task.id);
                      }}
                    >
                      Delete
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {data && data.results.length === 0 && (
              <tr>
                <td className="px-4 py-6 text-slate-400" colSpan={5}>
                  No tasks.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {showForm && <TaskFormModal onClose={() => setShowForm(false)} />}
    </div>
  );
}

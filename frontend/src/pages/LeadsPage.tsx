import { useState } from "react";

import { useDeleteLead, useLeads } from "../api/hooks";
import { useAuth } from "../auth/AuthContext";
import LeadFormModal from "../components/LeadFormModal";
import type { Lead, LeadStatus } from "../lib/types";

const STATUS_COLORS: Record<LeadStatus, string> = {
  new: "bg-slate-100 text-slate-700",
  contacted: "bg-blue-100 text-blue-700",
  qualified: "bg-amber-100 text-amber-700",
  unqualified: "bg-red-100 text-red-700",
  converted: "bg-green-100 text-green-700",
};

export default function LeadsPage() {
  const { hasRole } = useAuth();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const { data, isLoading, isError } = useLeads({
    search: search || undefined,
    status: status || undefined,
  });
  const del = useDeleteLead();

  const [editing, setEditing] = useState<Lead | null>(null);
  const [showForm, setShowForm] = useState(false);

  const canWrite = hasRole("sales_rep");
  const canDelete = hasRole("manager");

  function openCreate() {
    setEditing(null);
    setShowForm(true);
  }
  function openEdit(lead: Lead) {
    setEditing(lead);
    setShowForm(true);
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Leads</h1>
        {canWrite && (
          <button className="btn-primary" onClick={openCreate}>
            + New lead
          </button>
        )}
      </div>

      <div className="mb-4 flex gap-3">
        <input
          className="input max-w-xs"
          placeholder="Search name / email / company"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="input max-w-[180px]"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">All statuses</option>
          {(Object.keys(STATUS_COLORS) as LeadStatus[]).map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Company</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Owner</th>
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
            {isError && (
              <tr>
                <td className="px-4 py-6 text-red-500" colSpan={5}>
                  Failed to load leads.
                </td>
              </tr>
            )}
            {data?.results.map((lead) => (
              <tr key={lead.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-800">
                  {lead.name}
                  {lead.is_stale && (
                    <span className="ml-2 rounded bg-amber-50 px-1.5 py-0.5 text-xs text-amber-600">
                      stale
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-slate-600">{lead.company || "—"}</td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[lead.status]}`}
                  >
                    {lead.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-500">
                  {lead.owner_email ?? "—"}
                </td>
                <td className="px-4 py-3 text-right">
                  {canWrite && (
                    <button
                      className="text-brand-600 hover:underline"
                      onClick={() => openEdit(lead)}
                    >
                      Edit
                    </button>
                  )}
                  {canDelete && (
                    <button
                      className="ml-3 text-red-500 hover:underline"
                      onClick={() => {
                        if (confirm(`Delete lead "${lead.name}"?`))
                          del.mutate(lead.id);
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
                  No leads yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {showForm && (
        <LeadFormModal lead={editing} onClose={() => setShowForm(false)} />
      )}
    </div>
  );
}

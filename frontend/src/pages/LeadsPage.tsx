import { useRef, useState } from "react";

import {
  useBulkLeads,
  useDeleteLead,
  useImportLeads,
  useLeads,
  useTags,
} from "../api/hooks";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import LeadDetailDrawer from "../components/LeadDetailDrawer";
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
  const [tag, setTag] = useState("");
  const { data, isLoading } = useLeads({
    q: search || undefined,
    status: status || undefined,
    tag: tag ? Number(tag) : undefined,
  });
  const tags = useTags();
  const del = useDeleteLead();
  const bulk = useBulkLeads();
  const importLeads = useImportLeads();
  const fileRef = useRef<HTMLInputElement>(null);

  const [editing, setEditing] = useState<Lead | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [detailId, setDetailId] = useState<number | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());

  const canWrite = hasRole("sales_rep");
  const canDelete = hasRole("manager");
  const rows = data?.results ?? [];
  // Drive the drawer off live query data so tag/custom edits reflect immediately.
  const detailLead = detailId != null ? rows.find((l) => l.id === detailId) : undefined;

  function toggle(id: number) {
    setSelected((s) => {
      const next = new Set(s);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }
  function toggleAll() {
    setSelected((s) =>
      s.size === rows.length ? new Set() : new Set(rows.map((l) => l.id)),
    );
  }

  async function exportCsv() {
    const resp = await api.get("/api/leads/export/", {
      responseType: "blob",
      params: { q: search || undefined, status: status || undefined },
    });
    const url = URL.createObjectURL(resp.data as Blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "leads.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  const ids = [...selected];

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Leads</h1>
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={exportCsv}>
            Export CSV
          </button>
          {canWrite && (
            <>
              <button className="btn-ghost" onClick={() => fileRef.current?.click()}>
                Import CSV
              </button>
              <input
                ref={fileRef}
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file)
                    importLeads.mutate(file, {
                      onSuccess: (r) => alert(`Imported ${r.created} leads.`),
                      onSettled: () => fileRef.current && (fileRef.current.value = ""),
                    });
                }}
              />
              <button
                className="btn-primary"
                onClick={() => {
                  setEditing(null);
                  setShowForm(true);
                }}
              >
                + New lead
              </button>
            </>
          )}
        </div>
      </div>

      <div className="mb-4 flex gap-3">
        <input
          className="input max-w-xs"
          placeholder="Search (full-text)…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="input max-w-[160px]"
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
        <select
          className="input max-w-[160px]"
          value={tag}
          onChange={(e) => setTag(e.target.value)}
        >
          <option value="">All tags</option>
          {tags.data?.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
      </div>

      {/* Bulk action bar */}
      {selected.size > 0 && (
        <div className="mb-3 flex items-center gap-3 rounded-md bg-brand-50 px-4 py-2 text-sm">
          <span className="font-medium text-brand-700">{selected.size} selected</span>
          {canWrite && (
            <select
              className="input max-w-[180px]"
              defaultValue=""
              onChange={(e) => {
                if (e.target.value)
                  bulk.mutate(
                    { ids, action: "set_status", status: e.target.value },
                    { onSuccess: () => setSelected(new Set()) },
                  );
                e.target.value = "";
              }}
            >
              <option value="">Set status…</option>
              {(Object.keys(STATUS_COLORS) as LeadStatus[]).map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          )}
          {canDelete && (
            <button
              className="text-red-600 hover:underline"
              onClick={() => {
                if (confirm(`Delete ${selected.size} leads?`))
                  bulk.mutate(
                    { ids, action: "delete" },
                    { onSuccess: () => setSelected(new Set()) },
                  );
              }}
            >
              Delete
            </button>
          )}
          <button className="text-slate-500 hover:underline" onClick={() => setSelected(new Set())}>
            Clear
          </button>
        </div>
      )}

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">
                <input
                  type="checkbox"
                  checked={rows.length > 0 && selected.size === rows.length}
                  onChange={toggleAll}
                />
              </th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Tags</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Owner</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && (
              <tr>
                <td className="px-4 py-6 text-slate-400" colSpan={6}>
                  Loading…
                </td>
              </tr>
            )}
            {rows.map((lead) => (
              <tr key={lead.id} className="hover:bg-slate-50">
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selected.has(lead.id)}
                    onChange={() => toggle(lead.id)}
                  />
                </td>
                <td className="px-4 py-3 font-medium text-slate-800">
                  <button className="hover:underline" onClick={() => setDetailId(lead.id)}>
                    {lead.name}
                  </button>
                  {lead.is_stale && (
                    <span className="ml-2 rounded bg-amber-50 px-1.5 py-0.5 text-xs text-amber-600">
                      stale
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {lead.tags_detail.map((t) => (
                      <span
                        key={t.id}
                        className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600"
                      >
                        {t.name}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[lead.status]}`}
                  >
                    {lead.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-500">{lead.owner_email ?? "—"}</td>
                <td className="px-4 py-3 text-right">
                  {canWrite && (
                    <button
                      className="text-brand-600 hover:underline"
                      onClick={() => {
                        setEditing(lead);
                        setShowForm(true);
                      }}
                    >
                      Edit
                    </button>
                  )}
                  {canDelete && (
                    <button
                      className="ml-3 text-red-500 hover:underline"
                      onClick={() => {
                        if (confirm(`Delete lead "${lead.name}"?`)) del.mutate(lead.id);
                      }}
                    >
                      Delete
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {data && rows.length === 0 && (
              <tr>
                <td className="px-4 py-6 text-slate-400" colSpan={6}>
                  No leads found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {showForm && <LeadFormModal lead={editing} onClose={() => setShowForm(false)} />}
      {detailLead && (
        <LeadDetailDrawer lead={detailLead} onClose={() => setDetailId(null)} />
      )}
    </div>
  );
}

import { useState } from "react";

import { useCreateLead, useUpdateLead } from "../api/hooks";
import type { Lead, LeadStatus } from "../lib/types";
import Modal from "./Modal";

const STATUSES: LeadStatus[] = [
  "new",
  "contacted",
  "qualified",
  "unqualified",
  "converted",
];

export default function LeadFormModal({
  lead,
  onClose,
}: {
  lead: Lead | null; // null => create
  onClose: () => void;
}) {
  const create = useCreateLead();
  const update = useUpdateLead();
  const saving = create.isPending || update.isPending;

  const [form, setForm] = useState({
    name: lead?.name ?? "",
    email: lead?.email ?? "",
    company: lead?.company ?? "",
    status: lead?.status ?? ("new" as LeadStatus),
    source: lead?.source ?? "",
  });

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (lead) {
      await update.mutateAsync({ id: lead.id, ...form });
    } else {
      await create.mutateAsync(form);
    }
    onClose();
  }

  return (
    <Modal title={lead ? "Edit lead" : "New lead"} onClose={onClose}>
      <form onSubmit={onSubmit} className="space-y-3">
        <div>
          <label className="label">Name</label>
          <input
            className="input"
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
            required
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Email</label>
            <input
              className="input"
              type="email"
              value={form.email}
              onChange={(e) => set("email", e.target.value)}
            />
          </div>
          <div>
            <label className="label">Company</label>
            <input
              className="input"
              value={form.company}
              onChange={(e) => set("company", e.target.value)}
            />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Status</label>
            <select
              className="input"
              value={form.status}
              onChange={(e) => set("status", e.target.value as LeadStatus)}
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Source</label>
            <input
              className="input"
              value={form.source}
              onChange={(e) => set("source", e.target.value)}
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" className="btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-primary" disabled={saving}>
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

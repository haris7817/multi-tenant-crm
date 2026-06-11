import { useRef, useState } from "react";

import {
  useAttachments,
  useCustomFields,
  useCreateNote,
  useNotes,
  useTags,
  useUpdateLead,
  useUploadAttachment,
} from "../api/hooks";
import { useAuth } from "../auth/AuthContext";
import type { Lead } from "../lib/types";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border-t border-slate-200 px-5 py-4">
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
        {title}
      </h3>
      {children}
    </div>
  );
}

export default function LeadDetailDrawer({
  lead,
  onClose,
}: {
  lead: Lead;
  onClose: () => void;
}) {
  const { hasRole } = useAuth();
  const canWrite = hasRole("sales_rep");
  const target = { model: "lead", id: lead.id };

  const notes = useNotes(target);
  const addNote = useCreateNote();
  const attachments = useAttachments(target);
  const upload = useUploadAttachment();
  const allTags = useTags();
  const customFields = useCustomFields("lead");
  const updateLead = useUpdateLead();

  const [noteBody, setNoteBody] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const tagIds = new Set(lead.tags);

  function toggleTag(id: number) {
    const next = tagIds.has(id)
      ? lead.tags.filter((t) => t !== id)
      : [...lead.tags, id];
    updateLead.mutate({ id: lead.id, tags: next });
  }

  function setCustom(key: string, value: string) {
    updateLead.mutate({
      id: lead.id,
      custom: { ...(lead.custom ?? {}), [key]: value },
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40" onClick={onClose}>
      <div
        className="flex h-full w-full max-w-md flex-col overflow-y-auto bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-800">{lead.name}</h2>
            <p className="text-sm text-slate-500">{lead.company || "—"}</p>
          </div>
          <button className="text-slate-400 hover:text-slate-600" onClick={onClose}>
            ✕
          </button>
        </div>

        {/* Tags */}
        <Section title="Tags">
          <div className="flex flex-wrap gap-2">
            {allTags.data?.map((tag) => (
              <button
                key={tag.id}
                disabled={!canWrite}
                onClick={() => toggleTag(tag.id)}
                className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                  tagIds.has(tag.id)
                    ? "bg-brand-600 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {tag.name}
              </button>
            ))}
            {allTags.data?.length === 0 && (
              <span className="text-xs text-slate-400">No tags defined yet.</span>
            )}
          </div>
        </Section>

        {/* Custom fields */}
        {customFields.data && customFields.data.length > 0 && (
          <Section title="Custom fields">
            <div className="space-y-2">
              {customFields.data.map((f) => (
                <div key={f.id}>
                  <label className="label">{f.label}</label>
                  {f.field_type === "select" ? (
                    <select
                      className="input"
                      disabled={!canWrite}
                      value={String(lead.custom?.[f.key] ?? "")}
                      onChange={(e) => setCustom(f.key, e.target.value)}
                    >
                      <option value="">—</option>
                      {f.options.map((o) => (
                        <option key={o} value={o}>
                          {o}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      className="input"
                      type={f.field_type === "number" ? "number" : f.field_type === "date" ? "date" : "text"}
                      disabled={!canWrite}
                      defaultValue={String(lead.custom?.[f.key] ?? "")}
                      onBlur={(e) => setCustom(f.key, e.target.value)}
                    />
                  )}
                </div>
              ))}
            </div>
          </Section>
        )}

        {/* Notes */}
        <Section title="Notes">
          {canWrite && (
            <div className="mb-3 flex gap-2">
              <input
                className="input"
                placeholder="Add a note…"
                value={noteBody}
                onChange={(e) => setNoteBody(e.target.value)}
              />
              <button
                className="btn-primary"
                disabled={!noteBody.trim() || addNote.isPending}
                onClick={() =>
                  addNote.mutate(
                    { body: noteBody, target_model: "lead", target_id: lead.id },
                    { onSuccess: () => setNoteBody("") },
                  )
                }
              >
                Add
              </button>
            </div>
          )}
          <div className="space-y-2">
            {notes.data?.map((n) => (
              <div key={n.id} className="rounded-md bg-slate-50 p-2 text-sm">
                <div className="text-slate-700">{n.body}</div>
                <div className="mt-1 text-xs text-slate-400">
                  {n.author_email ?? "system"} · {new Date(n.created_at).toLocaleString()}
                </div>
              </div>
            ))}
            {notes.data?.length === 0 && (
              <p className="text-xs text-slate-400">No notes yet.</p>
            )}
          </div>
        </Section>

        {/* Attachments */}
        <Section title="Attachments">
          {canWrite && (
            <div className="mb-3">
              <input
                ref={fileRef}
                type="file"
                className="text-sm"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file)
                    upload.mutate(
                      { file, target_model: "lead", target_id: lead.id },
                      { onSuccess: () => fileRef.current && (fileRef.current.value = "") },
                    );
                }}
              />
            </div>
          )}
          <div className="space-y-1">
            {attachments.data?.map((a) => (
              <a
                key={a.id}
                href={a.url ?? "#"}
                target="_blank"
                rel="noreferrer"
                className="block text-sm text-brand-600 hover:underline"
              >
                {a.filename}
              </a>
            ))}
            {attachments.data?.length === 0 && (
              <p className="text-xs text-slate-400">No attachments.</p>
            )}
          </div>
        </Section>
      </div>
    </div>
  );
}

import { Sparkles, X } from "lucide-react";
import { useState } from "react";

/**
 * Floating AI assistant entry point (brand spec §11). The conversational
 * assistant ships in Phase 14; this is the styled entry point + placeholder.
 */
export default function AIAssistantButton() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {open && (
        <div className="fixed bottom-24 right-6 z-50 w-80 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-pop">
          <div className="flex items-center justify-between bg-gradient-to-r from-ai-600 to-brand-600 px-4 py-3 text-white">
            <div className="flex items-center gap-2 font-semibold">
              <Sparkles size={18} /> AI Assistant
            </div>
            <button onClick={() => setOpen(false)} aria-label="Close">
              <X size={18} />
            </button>
          </div>
          <div className="space-y-3 p-4 text-sm text-slate-600">
            <p>
              Ask about your CRM in plain language — “show stale deals in
              negotiation over $5k”, “summarize this lead”, “draft a follow-up”.
            </p>
            <div className="rounded-lg bg-ai-100/60 px-3 py-2 text-xs font-medium text-ai-700">
              ✨ Coming in Phase 14 — permission-aware, tenant-isolated, fully audited.
            </div>
            <input className="input" placeholder="Ask the assistant…" disabled />
          </div>
        </div>
      )}

      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="AI Assistant"
        className="fixed bottom-6 right-6 z-50 grid h-14 w-14 place-items-center rounded-full bg-gradient-to-br from-ai-500 to-ai-700 text-white shadow-pop transition-transform hover:scale-105 active:scale-95"
      >
        <Sparkles size={24} />
      </button>
    </>
  );
}

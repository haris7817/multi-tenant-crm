import { useState } from "react";

import { useMoveDeal, usePipeline } from "../api/hooks";
import { useAuth } from "../auth/AuthContext";
import DealFormModal from "../components/DealFormModal";
import type { Deal, PipelineColumn } from "../lib/types";

function money(v: string | number) {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(Number(v));
}

export default function PipelinePage() {
  const { hasRole } = useAuth();
  const { data: columns, isLoading } = usePipeline();
  const move = useMoveDeal();
  const [showForm, setShowForm] = useState(false);
  const [dragId, setDragId] = useState<number | null>(null);

  const canMove = hasRole("sales_rep");

  function onDrop(stageId: number) {
    if (dragId != null && canMove) {
      move.mutate({ id: dragId, stage: stageId });
    }
    setDragId(null);
  }

  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <div>
          <h1>Pipeline</h1>
          {canMove && (
            <p className="mt-1 text-sm text-slate-500">
              Drag a card between columns to move the deal.
            </p>
          )}
        </div>
        {canMove && (
          <button className="btn-primary" onClick={() => setShowForm(true)}>
            + New deal
          </button>
        )}
      </div>

      {isLoading && <p className="text-slate-400">Loading…</p>}

      <div className="mt-4 flex gap-4 overflow-x-auto pb-4">
        {columns?.map((col: PipelineColumn) => {
          const total = col.deals.reduce((s, d) => s + Number(d.value), 0);
          const accent = col.stage.is_won
            ? "bg-emerald-500"
            : col.stage.is_lost
              ? "bg-red-400"
              : "bg-brand-500";
          return (
            <div
              key={col.stage.id}
              className="flex w-72 shrink-0 flex-col rounded-xl bg-slate-100/70"
              onDragOver={(e) => canMove && e.preventDefault()}
              onDrop={() => onDrop(col.stage.id)}
            >
              <div className="flex items-center justify-between px-3 py-2.5">
                <span className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                  <span className={`h-2 w-2 rounded-full ${accent}`} />
                  {col.stage.name}
                  <span className="rounded-full bg-white px-1.5 text-xs font-medium text-slate-500">
                    {col.deals.length}
                  </span>
                </span>
                <span className="text-xs font-medium text-slate-500">
                  {money(total)}
                </span>
              </div>
              <div className="flex-1 space-y-2 px-2 pb-2">
                {col.deals.map((deal: Deal) => (
                  <div
                    key={deal.id}
                    draggable={canMove}
                    onDragStart={() => setDragId(deal.id)}
                    className={`card card-hover p-3 ${canMove ? "cursor-grab active:cursor-grabbing" : ""}`}
                  >
                    <div className="text-sm font-semibold text-slate-800">
                      {deal.title}
                    </div>
                    <div className="mt-2 flex items-center justify-between">
                      <span className="badge-blue">{money(deal.value)}</span>
                      {deal.owner && (
                        <span className="grid h-6 w-6 place-items-center rounded-full bg-slate-200 text-[10px] font-bold text-slate-600">
                          {String(deal.owner).slice(0, 2)}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
                {col.deals.length === 0 && (
                  <div className="px-1 py-6 text-center text-xs text-slate-400">
                    Drop deals here
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {showForm && <DealFormModal onClose={() => setShowForm(false)} />}
    </div>
  );
}

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
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Pipeline</h1>
        {canMove && (
          <button className="btn-primary" onClick={() => setShowForm(true)}>
            + New deal
          </button>
        )}
      </div>

      {isLoading && <p className="text-slate-400">Loading…</p>}

      <div className="flex gap-4 overflow-x-auto pb-4">
        {columns?.map((col: PipelineColumn) => {
          const total = col.deals.reduce((s, d) => s + Number(d.value), 0);
          return (
            <div
              key={col.stage.id}
              className="flex w-72 shrink-0 flex-col rounded-lg bg-slate-100"
              onDragOver={(e) => canMove && e.preventDefault()}
              onDrop={() => onDrop(col.stage.id)}
            >
              <div className="flex items-center justify-between px-3 py-2">
                <span className="text-sm font-semibold text-slate-700">
                  {col.stage.name}
                  {col.stage.is_won && " 🏆"}
                  {col.stage.is_lost && " ✖"}
                </span>
                <span className="text-xs text-slate-500">
                  {col.deals.length} · {money(total)}
                </span>
              </div>
              <div className="flex-1 space-y-2 px-2 pb-2">
                {col.deals.map((deal: Deal) => (
                  <div
                    key={deal.id}
                    draggable={canMove}
                    onDragStart={() => setDragId(deal.id)}
                    className={`card p-3 ${canMove ? "cursor-grab active:cursor-grabbing" : ""}`}
                  >
                    <div className="text-sm font-medium text-slate-800">
                      {deal.title}
                    </div>
                    <div className="mt-1 text-xs text-slate-500">
                      {money(deal.value)}
                    </div>
                  </div>
                ))}
                {col.deals.length === 0 && (
                  <div className="px-1 py-4 text-center text-xs text-slate-400">
                    Drop deals here
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {canMove && (
        <p className="mt-2 text-xs text-slate-400">
          Drag a card to another column to move the deal.
        </p>
      )}

      {showForm && <DealFormModal onClose={() => setShowForm(false)} />}
    </div>
  );
}

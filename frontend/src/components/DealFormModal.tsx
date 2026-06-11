import { useState } from "react";

import { useCreateDeal, useStages } from "../api/hooks";
import Modal from "./Modal";

export default function DealFormModal({ onClose }: { onClose: () => void }) {
  const { data: stages } = useStages();
  const create = useCreateDeal();

  const [title, setTitle] = useState("");
  const [value, setValue] = useState("0");
  const [stage, setStage] = useState<number | "">("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (stage === "") return;
    await create.mutateAsync({ title, value, stage: Number(stage) });
    onClose();
  }

  return (
    <Modal title="New deal" onClose={onClose}>
      <form onSubmit={onSubmit} className="space-y-3">
        <div>
          <label className="label">Title</label>
          <input
            className="input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Value</label>
            <input
              className="input"
              type="number"
              min="0"
              step="0.01"
              value={value}
              onChange={(e) => setValue(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Stage</label>
            <select
              className="input"
              value={stage}
              onChange={(e) => setStage(e.target.value ? Number(e.target.value) : "")}
              required
            >
              <option value="">Select…</option>
              {stages?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" className="btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-primary" disabled={create.isPending}>
            {create.isPending ? "Saving…" : "Create"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

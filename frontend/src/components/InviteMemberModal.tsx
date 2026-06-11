import { useState } from "react";
import { AxiosError } from "axios";

import { useInviteMember } from "../api/hooks";
import type { Role } from "../lib/types";
import Modal from "./Modal";

const ROLES: Role[] = ["viewer", "sales_rep", "manager", "admin", "owner"];

export default function InviteMemberModal({ onClose }: { onClose: () => void }) {
  const invite = useInviteMember();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Role>("viewer");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await invite.mutateAsync({ email, role, password });
      onClose();
    } catch (err) {
      const ax = err as AxiosError<Record<string, unknown>>;
      const detail = ax.response?.data
        ? JSON.stringify(ax.response.data)
        : "Invite failed.";
      setError(detail);
    }
  }

  return (
    <Modal title="Invite member" onClose={onClose}>
      <form onSubmit={onSubmit} className="space-y-3">
        <div>
          <label className="label">Email</label>
          <input
            className="input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Role</label>
            <select
              className="input"
              value={role}
              onChange={(e) => setRole(e.target.value as Role)}
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Temp password</label>
            <input
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" className="btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-primary" disabled={invite.isPending}>
            {invite.isPending ? "Inviting…" : "Invite"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

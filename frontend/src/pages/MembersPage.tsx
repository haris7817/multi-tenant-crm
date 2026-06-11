import { useState } from "react";

import { useMembers, useRemoveMember, useUpdateMemberRole } from "../api/hooks";
import { useAuth } from "../auth/AuthContext";
import InviteMemberModal from "../components/InviteMemberModal";
import type { Role } from "../lib/types";

const ROLES: Role[] = ["viewer", "sales_rep", "manager", "admin", "owner"];

export default function MembersPage() {
  const { hasRole } = useAuth();
  const { data: members, isLoading } = useMembers();
  const updateRole = useUpdateMemberRole();
  const remove = useRemoveMember();
  const [showInvite, setShowInvite] = useState(false);

  const canManage = hasRole("admin");

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Members</h1>
        {canManage && (
          <button className="btn-primary" onClick={() => setShowInvite(true)}>
            + Invite member
          </button>
        )}
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && (
              <tr>
                <td className="px-4 py-6 text-slate-400" colSpan={4}>
                  Loading…
                </td>
              </tr>
            )}
            {members?.map((m) => (
              <tr key={m.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-800">{m.email}</td>
                <td className="px-4 py-3 text-slate-600">{m.full_name || "—"}</td>
                <td className="px-4 py-3">
                  {canManage ? (
                    <select
                      className="input max-w-[150px]"
                      value={m.role}
                      onChange={(e) =>
                        updateRole.mutate({
                          id: m.id,
                          role: e.target.value as Role,
                        })
                      }
                    >
                      {ROLES.map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium uppercase text-slate-600">
                      {m.role}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  {canManage && (
                    <button
                      className="text-red-500 hover:underline"
                      onClick={() => {
                        if (confirm(`Remove ${m.email}?`)) remove.mutate(m.id);
                      }}
                    >
                      Remove
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showInvite && <InviteMemberModal onClose={() => setShowInvite(false)} />}
    </div>
  );
}

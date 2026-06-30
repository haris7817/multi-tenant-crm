import { useState } from "react";

import { useApiKeys, useCreateApiKey, useRevokeApiKey } from "../api/hooks";
import type { ApiKeyCreated } from "../lib/types";

export default function ApiKeysPage() {
  const keys = useApiKeys();
  const create = useCreateApiKey();
  const revoke = useRevokeApiKey();

  const [name, setName] = useState("");
  const [scopes, setScopes] = useState<string[]>(["read"]);
  const [created, setCreated] = useState<ApiKeyCreated | null>(null);

  function toggleScope(s: string) {
    setScopes((cur) =>
      cur.includes(s) ? cur.filter((x) => x !== s) : [...cur, s],
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const result = await create.mutateAsync({ name, scopes });
    setCreated(result);
    setName("");
    setScopes(["read"]);
  }

  return (
    <div>
      <div className="mb-4">
        <h1>API Keys</h1>
        <p className="text-sm text-slate-500">
          Programmatic access for external apps. Use header{" "}
          <code>Authorization: Api-Key &lt;key&gt;</code> against{" "}
          <code>/api/v1/</code>.
        </p>
      </div>

      {/* The freshly created secret — shown once */}
      {created && (
        <div className="mb-4 rounded-md border border-amber-300 bg-amber-50 p-4">
          <p className="text-sm font-medium text-amber-800">
            Copy your new key now — it won't be shown again.
          </p>
          <div className="mt-2 flex items-center gap-2">
            <code className="flex-1 break-all rounded bg-white px-2 py-1 text-sm">
              {created.key}
            </code>
            <button
              className="btn-ghost"
              onClick={() => navigator.clipboard?.writeText(created.key)}
            >
              Copy
            </button>
            <button className="btn-ghost" onClick={() => setCreated(null)}>
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Create form */}
      <form onSubmit={submit} className="card mb-6 flex flex-wrap items-end gap-3 p-4">
        <div className="flex-1 min-w-[200px]">
          <label className="label">Name</label>
          <input
            className="input"
            placeholder="e.g. Zapier integration"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="label">Scopes</label>
          <div className="flex gap-3 py-2">
            {["read", "write"].map((s) => (
              <label key={s} className="flex items-center gap-1 text-sm">
                <input
                  type="checkbox"
                  checked={scopes.includes(s)}
                  onChange={() => toggleScope(s)}
                />
                {s}
              </label>
            ))}
          </div>
        </div>
        <button className="btn-primary" disabled={create.isPending || !scopes.length}>
          {create.isPending ? "Creating…" : "Create key"}
        </button>
      </form>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Prefix</th>
              <th className="px-4 py-3">Scopes</th>
              <th className="px-4 py-3">Last used</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {keys.data?.map((k) => (
              <tr key={k.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-800">{k.name}</td>
                <td className="px-4 py-3 font-mono text-slate-500">{k.prefix}</td>
                <td className="px-4 py-3 text-slate-600">{k.scopes.join(", ")}</td>
                <td className="px-4 py-3 text-slate-500">
                  {k.last_used_at ? new Date(k.last_used_at).toLocaleString() : "never"}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      k.is_active
                        ? "bg-green-100 text-green-700"
                        : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {k.is_active ? "active" : "revoked"}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  {k.is_active && (
                    <button
                      className="text-red-500 hover:underline"
                      onClick={() => {
                        if (confirm(`Revoke key "${k.name}"?`)) revoke.mutate(k.id);
                      }}
                    >
                      Revoke
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {keys.data && keys.data.length === 0 && (
              <tr>
                <td className="px-4 py-6 text-slate-400" colSpan={6}>
                  No API keys yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

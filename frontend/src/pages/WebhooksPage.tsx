import { useState } from "react";

import {
  useCreateInboundEndpoint,
  useCreateWebhook,
  useDeleteInboundEndpoint,
  useDeleteWebhook,
  useInboundEndpoints,
  useReplayDelivery,
  useWebhookDeliveries,
  useWebhooks,
} from "../api/hooks";
import { WEBHOOK_EVENTS, type WebhookEndpoint } from "../lib/types";

const STATUS_COLORS: Record<string, string> = {
  success: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  pending: "bg-amber-100 text-amber-700",
};

export default function WebhooksPage() {
  const endpoints = useWebhooks();
  const deliveries = useWebhookDeliveries();
  const create = useCreateWebhook();
  const del = useDeleteWebhook();
  const replay = useReplayDelivery();
  const inbound = useInboundEndpoints();
  const createInbound = useCreateInboundEndpoint();
  const deleteInbound = useDeleteInboundEndpoint();
  const [inboundSource, setInboundSource] = useState("");

  const [url, setUrl] = useState("");
  const [events, setEvents] = useState<string[]>(["lead.created"]);
  const [created, setCreated] = useState<WebhookEndpoint | null>(null);

  function toggle(e: string) {
    setEvents((cur) => (cur.includes(e) ? cur.filter((x) => x !== e) : [...cur, e]));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const result = await create.mutateAsync({ url, events });
    setCreated(result);
    setUrl("");
    setEvents(["lead.created"]);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Webhooks</h1>
        <p className="text-sm text-slate-500">
          We POST signed events to your URL. Verify with the{" "}
          <code>X-Webhook-Signature</code> (HMAC-SHA256 of the body using the secret).
        </p>
      </div>

      {created && (
        <div className="rounded-md border border-amber-300 bg-amber-50 p-4">
          <p className="text-sm font-medium text-amber-800">
            Signing secret for {created.url} — store it to verify signatures:
          </p>
          <code className="mt-1 block break-all rounded bg-white px-2 py-1 text-sm">
            {created.secret}
          </code>
          <button className="btn-ghost mt-2" onClick={() => setCreated(null)}>
            Dismiss
          </button>
        </div>
      )}

      {/* Create endpoint */}
      <form onSubmit={submit} className="card space-y-3 p-4">
        <div>
          <label className="label">Endpoint URL</label>
          <input
            className="input"
            placeholder="https://example.com/webhooks/crm"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="label">Events</label>
          <div className="flex flex-wrap gap-2">
            {WEBHOOK_EVENTS.map((e) => (
              <label
                key={e}
                className={`cursor-pointer rounded-full px-2.5 py-1 text-xs font-medium ${
                  events.includes(e)
                    ? "bg-brand-600 text-white"
                    : "bg-slate-100 text-slate-600"
                }`}
              >
                <input
                  type="checkbox"
                  className="hidden"
                  checked={events.includes(e)}
                  onChange={() => toggle(e)}
                />
                {e}
              </label>
            ))}
          </div>
        </div>
        <div>
          <button className="btn-primary" disabled={create.isPending || !events.length}>
            {create.isPending ? "Creating…" : "Add endpoint"}
          </button>
        </div>
      </form>

      {/* Endpoints */}
      <div className="card overflow-hidden">
        <div className="border-b border-slate-100 px-4 py-2 text-sm font-semibold text-slate-700">
          Endpoints
        </div>
        <table className="w-full text-sm">
          <tbody className="divide-y divide-slate-100">
            {endpoints.data?.map((ep) => (
              <tr key={ep.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-800">{ep.url}</td>
                <td className="px-4 py-3 text-xs text-slate-500">
                  {ep.events.join(", ") || "all"}
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    className="text-red-500 hover:underline"
                    onClick={() => {
                      if (confirm(`Delete endpoint ${ep.url}?`)) del.mutate(ep.id);
                    }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {endpoints.data && endpoints.data.length === 0 && (
              <tr>
                <td className="px-4 py-6 text-slate-400">No endpoints yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Recent deliveries */}
      <div className="card overflow-hidden">
        <div className="border-b border-slate-100 px-4 py-2 text-sm font-semibold text-slate-700">
          Recent deliveries
        </div>
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-2">Event</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">HTTP</th>
              <th className="px-4 py-2">Attempts</th>
              <th className="px-4 py-2"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {deliveries.data?.map((d) => (
              <tr key={d.id} className="hover:bg-slate-50">
                <td className="px-4 py-2 font-mono text-xs">{d.event_type}</td>
                <td className="px-4 py-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[d.status]}`}
                  >
                    {d.status}
                  </span>
                </td>
                <td className="px-4 py-2 text-slate-500">{d.response_status ?? "—"}</td>
                <td className="px-4 py-2 text-slate-500">{d.attempts}</td>
                <td className="px-4 py-2 text-right">
                  {d.status === "failed" && (
                    <button
                      className="text-brand-600 hover:underline"
                      onClick={() => replay.mutate(d.id)}
                    >
                      Replay
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {deliveries.data && deliveries.data.length === 0 && (
              <tr>
                <td className="px-4 py-6 text-slate-400" colSpan={5}>
                  No deliveries yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Inbound endpoints (11.6) */}
      <div className="card overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-100 px-4 py-2">
          <span className="text-sm font-semibold text-slate-700">
            Inbound endpoints (partners → us)
          </span>
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              createInbound.mutate(
                { source: inboundSource || "inbound", action: "create_lead" },
                { onSuccess: () => setInboundSource("") },
              );
            }}
          >
            <input
              className="input max-w-[160px] py-1"
              placeholder="source e.g. typeform"
              value={inboundSource}
              onChange={(e) => setInboundSource(e.target.value)}
            />
            <button className="btn-primary" disabled={createInbound.isPending}>
              + Add
            </button>
          </form>
        </div>
        <div className="divide-y divide-slate-100">
          {inbound.data?.map((ep) => (
            <div key={ep.id} className="px-4 py-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium text-slate-800">
                  {ep.source || ep.action}
                </span>
                <button
                  className="text-red-500 hover:underline"
                  onClick={() => {
                    if (confirm("Delete inbound endpoint?")) deleteInbound.mutate(ep.id);
                  }}
                >
                  Delete
                </button>
              </div>
              <div className="mt-1 space-y-0.5 text-xs text-slate-500">
                <div>
                  POST URL: <code>{ep.receive_url}</code>
                </div>
                <div>
                  Secret: <code className="break-all">{ep.secret}</code> (sign body
                  with HMAC-SHA256 → <code>X-Signature: sha256=…</code>)
                </div>
              </div>
            </div>
          ))}
          {inbound.data && inbound.data.length === 0 && (
            <div className="px-4 py-6 text-slate-400">No inbound endpoints.</div>
          )}
        </div>
      </div>
    </div>
  );
}

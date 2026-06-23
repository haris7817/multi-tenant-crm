import {
  useAuthorizeConnection,
  useConnectionProviders,
  useConnections,
  useDisconnect,
} from "../api/hooks";

export default function IntegrationsPage() {
  const providers = useConnectionProviders();
  const connections = useConnections();
  const authorize = useAuthorizeConnection();
  const disconnect = useDisconnect();

  const byProvider = new Map(connections.data?.map((c) => [c.provider, c]));

  async function connect(provider: string) {
    const redirectUri = `${window.location.origin}/oauth/callback`;
    const { authorize_url } = await authorize.mutateAsync({
      provider,
      redirect_uri: redirectUri,
    });
    // Hand off to the provider's consent screen.
    window.location.href = authorize_url;
  }

  return (
    <div>
      <div className="mb-4">
        <h1>Integrations</h1>
        <p className="text-sm text-slate-500">
          Connect external services. Tokens are stored encrypted; we never show them.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {providers.data?.map((p) => {
          const conn = byProvider.get(p.key);
          return (
            <div key={p.key} className="card flex items-center justify-between p-4">
              <div>
                <div className="font-medium text-slate-800">{p.label}</div>
                <div className="mt-0.5 text-xs text-slate-500">
                  {p.connected
                    ? `Connected${conn?.account_email ? ` · ${conn.account_email}` : ""}`
                    : p.configured
                      ? "Not connected"
                      : "Not configured (set client id/secret in env)"}
                </div>
              </div>
              {p.connected && conn ? (
                <button
                  className="btn-ghost"
                  onClick={() => {
                    if (confirm(`Disconnect ${p.label}?`)) disconnect.mutate(conn.id);
                  }}
                >
                  Disconnect
                </button>
              ) : (
                <button
                  className="btn-primary"
                  disabled={!p.configured || authorize.isPending}
                  onClick={() => connect(p.key)}
                >
                  Connect
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

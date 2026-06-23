import { useBillingPlans, useBillingStatus, useCheckout } from "../api/hooks";

function money(cents: number) {
  return cents === 0 ? "Free" : `$${(cents / 100).toFixed(0)}/mo`;
}

function UsageBar({
  label,
  used,
  limit,
}: {
  label: string;
  used: number;
  limit: number | null;
}) {
  const pct = limit ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  const over = limit !== null && used >= limit;
  return (
    <div>
      <div className="flex justify-between text-sm">
        <span className="text-slate-600">{label}</span>
        <span className="text-slate-500">
          {used} / {limit ?? "∞"}
        </span>
      </div>
      <div className="mt-1 h-2 rounded-full bg-slate-100">
        <div
          className={`h-2 rounded-full ${over ? "bg-red-500" : "bg-brand-500"}`}
          style={{ width: `${limit ? pct : 6}%` }}
        />
      </div>
    </div>
  );
}

export default function BillingPage() {
  const status = useBillingStatus();
  const plans = useBillingPlans();
  const checkout = useCheckout();

  const s = status.data;

  async function upgrade(plan: string) {
    try {
      const { checkout_url } = await checkout.mutateAsync(plan);
      window.location.href = checkout_url;
    } catch {
      alert("Checkout isn't available — Stripe isn't configured in this environment.");
    }
  }

  return (
    <div className="space-y-6">
      <h1>Billing</h1>

      {/* Current plan + usage */}
      <div className="card p-5">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs uppercase tracking-wide text-slate-500">
              Current plan
            </div>
            <div className="text-xl font-bold text-slate-800">
              {s?.plan_name ?? "—"}
            </div>
          </div>
          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium uppercase text-slate-600">
            {s?.status ?? "—"}
          </span>
        </div>
        {s && (
          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
            <UsageBar label="Leads" used={s.usage.leads} limit={s.limits.leads} />
            <UsageBar label="Members" used={s.usage.members} limit={s.limits.members} />
          </div>
        )}
      </div>

      {/* Plans */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {plans.data?.map((p) => {
          const current = s?.plan === p.key;
          return (
            <div key={p.key} className="card flex flex-col p-5">
              <div className="text-lg font-semibold text-slate-800">{p.name}</div>
              <div className="mt-1 text-2xl font-bold text-brand-700">
                {money(p.price_cents)}
              </div>
              <ul className="mt-3 flex-1 space-y-1 text-sm text-slate-600">
                <li>{p.max_leads ?? "Unlimited"} leads</li>
                <li>{p.max_members ?? "Unlimited"} members</li>
              </ul>
              <div className="mt-4">
                {current ? (
                  <span className="btn-ghost w-full justify-center">Current plan</span>
                ) : p.price_cents > 0 ? (
                  <button
                    className="btn-primary w-full"
                    disabled={checkout.isPending}
                    onClick={() => upgrade(p.key)}
                  >
                    Upgrade
                  </button>
                ) : (
                  <span className="text-xs text-slate-400">—</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

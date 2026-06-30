import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import GoogleSignInButton from "../components/GoogleSignInButton";

export default function LoginPage() {
  const { login, loginWithGoogle, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [slug, setSlug] = useState("acme");
  const [email, setEmail] = useState("owner@acme.crm.local");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(slug.trim(), email.trim(), password);
      navigate("/", { replace: true });
    } catch {
      setError("Login failed — check the workspace, email, and password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 via-brand-50/40 to-ai-100/30 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center text-center">
          <div className="grid h-12 w-12 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-lg font-extrabold text-white shadow-pop">
            ⬡
          </div>
          <h1 className="mt-3 text-2xl font-bold text-slate-900">Welcome back</h1>
          <p className="mt-1 text-sm text-slate-500">
            Sign in to your CRM workspace.
          </p>
        </div>

        <div className="card p-6">
          <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="label">Workspace</label>
            <input
              className="input"
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              placeholder="acme"
              autoFocus
            />
            <p className="mt-1 text-xs text-slate-400">
              Your tenant subdomain, e.g. <code>acme</code> or <code>globex</code>.
            </p>
          </div>
          <div>
            <label className="label">Email</label>
            <input
              className="input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button className="btn-primary w-full" disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <div className="my-4 flex items-center gap-2 text-xs text-slate-400">
          <span className="h-px flex-1 bg-slate-200" /> or{" "}
          <span className="h-px flex-1 bg-slate-200" />
        </div>
        <GoogleSignInButton
          onCredential={async (credential) => {
            setError(null);
            try {
              await loginWithGoogle(slug.trim(), credential);
              navigate("/", { replace: true });
            } catch {
              setError("Google sign-in failed — no account in this workspace?");
            }
          }}
        />
        </div>

        <p className="mt-4 text-center text-xs text-slate-400">
          Demo: workspace <code>acme</code> · owner@acme.crm.local · password123
        </p>
      </div>
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useCompleteOAuth } from "../api/hooks";

export default function OAuthCallbackPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const complete = useCompleteOAuth();
  const [error, setError] = useState<string | null>(null);
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return; // guard against double-run in StrictMode
    ran.current = true;
    const state = params.get("state");
    const code = params.get("code");
    if (!state || !code) {
      setError("Missing state or code in callback.");
      return;
    }
    complete.mutate(
      { state, code },
      {
        onSuccess: () => navigate("/integrations", { replace: true }),
        onError: () => setError("Could not complete the connection."),
      },
    );
  }, [complete, navigate, params]);

  return (
    <div className="flex h-64 items-center justify-center text-slate-500">
      {error ? (
        <div className="text-center">
          <p className="text-red-600">{error}</p>
          <button className="btn-ghost mt-3" onClick={() => navigate("/integrations")}>
            Back to Integrations
          </button>
        </div>
      ) : (
        "Completing connection…"
      )}
    </div>
  );
}

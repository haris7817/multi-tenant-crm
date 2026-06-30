import axios from "axios";
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import type { Role } from "../lib/types";
import { type AuthState, clearAuth, getAuth, setAuth } from "./storage";

interface AuthContextValue {
  auth: AuthState | null;
  isAuthenticated: boolean;
  login: (slug: string, email: string, password: string) => Promise<void>;
  loginWithGoogle: (slug: string, credential: string) => Promise<void>;
  logout: () => void;
  hasRole: (min: Role) => boolean;
}

const ROLE_LEVEL: Record<Role, number> = {
  owner: 4,
  admin: 3,
  manager: 2,
  sales_rep: 1,
  viewer: 0,
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuthState] = useState<AuthState | null>(() => getAuth());

  // Shared: turn a token response into stored auth state (+ fetch tenant name).
  const persist = useCallback(async (slug: string, data: any) => {
    const headers = { "X-Tenant": slug };
    let tenantName = slug;
    try {
      const t = await axios.get("/api/tenant/", { headers });
      tenantName = t.data.name;
    } catch {
      /* fall back to slug */
    }
    const state: AuthState = {
      slug,
      tenantName,
      email: data.email,
      role: data.role,
      access: data.access,
      refresh: data.refresh,
    };
    setAuth(state);
    setAuthState(state);
  }, []);

  const login = useCallback(
    async (slug: string, email: string, password: string) => {
      // Same-origin call; the Vite proxy maps X-Tenant -> Host subdomain.
      const { data } = await axios.post(
        "/api/auth/login/",
        { email, password },
        { headers: { "X-Tenant": slug } },
      );
      await persist(slug, data);
    },
    [persist],
  );

  const loginWithGoogle = useCallback(
    async (slug: string, credential: string) => {
      const { data } = await axios.post(
        "/api/auth/google/",
        { credential },
        { headers: { "X-Tenant": slug } },
      );
      await persist(slug, data);
    },
    [persist],
  );

  const logout = useCallback(() => {
    clearAuth();
    setAuthState(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      auth,
      isAuthenticated: !!auth,
      login,
      loginWithGoogle,
      logout,
      hasRole: (min: Role) =>
        !!auth && ROLE_LEVEL[auth.role] >= ROLE_LEVEL[min],
    }),
    [auth, login, loginWithGoogle, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

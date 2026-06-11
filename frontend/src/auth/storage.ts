// Small non-React store for auth state so the Axios client can read it too.
import type { Role } from "../lib/types";

export interface AuthState {
  slug: string; // tenant subdomain label, e.g. "acme"
  tenantName: string;
  email: string;
  role: Role;
  access: string;
  refresh: string;
}

const KEY = "crm.auth";

export function getAuth(): AuthState | null {
  const raw = localStorage.getItem(KEY);
  return raw ? (JSON.parse(raw) as AuthState) : null;
}

export function setAuth(state: AuthState) {
  localStorage.setItem(KEY, JSON.stringify(state));
}

export function setAccess(access: string) {
  const auth = getAuth();
  if (auth) setAuth({ ...auth, access });
}

export function clearAuth() {
  localStorage.removeItem(KEY);
}

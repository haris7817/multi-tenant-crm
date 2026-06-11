import axios, {
  AxiosError,
  type InternalAxiosRequestConfig,
} from "axios";

import { clearAuth, getAuth, setAccess } from "../auth/storage";

// The SPA calls the API same-origin (/api/*); the Vite dev proxy injects the
// tenant as the Host header from the X-Tenant header we attach here. So the
// client is "tenant-aware" via X-Tenant + the JWT, with no cross-origin calls.
export const api = axios.create();

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const auth = getAuth();
  if (auth) {
    config.headers["X-Tenant"] = auth.slug;
    config.headers.Authorization = `Bearer ${auth.access}`;
  }
  return config;
});

// Refresh the access token on a 401, once, then retry the original request.
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccess(): Promise<string | null> {
  const auth = getAuth();
  if (!auth) return null;
  try {
    const resp = await axios.post(
      "/api/auth/refresh/",
      { refresh: auth.refresh },
      { headers: { "X-Tenant": auth.slug } },
    );
    const access = resp.data.access as string;
    setAccess(access);
    return access;
  } catch {
    return null;
  }
}

api.interceptors.response.use(
  (resp) => resp,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };
    if (error.response?.status === 401 && original && !original._retry) {
      original._retry = true;
      refreshPromise = refreshPromise ?? refreshAccess();
      const access = await refreshPromise;
      refreshPromise = null;
      if (access) {
        original.headers.Authorization = `Bearer ${access}`;
        return api(original);
      }
      clearAuth();
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

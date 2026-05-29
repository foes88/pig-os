import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

// ── Request: inject Authorization header ─────────────────────────────────────
// Lazy import to avoid circular dependency (store imports client, client imports store)
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    try {
      const raw = localStorage.getItem("pigos-auth");
      if (raw) {
        const { state } = JSON.parse(raw) as { state: { accessToken: string | null } };
        if (state?.accessToken) {
          config.headers.Authorization = `Bearer ${state.accessToken}`;
        }
      }
    } catch {
      // Corrupt storage — handled by 401 response interceptor
    }
  }
  return config;
});

// ── Response: 401 refresh, 402 upgrade modal ──────────────────────────────────
let _refreshing: Promise<string> | null = null;

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // 401 → attempt token refresh once
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;

      if (!_refreshing) {
        _refreshing = _doRefresh().finally(() => { _refreshing = null; });
      }

      try {
        const newToken = await _refreshing;
        original.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(original);
      } catch {
        _clearAuth();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
    }

    // 402 → open upgrade modal
    if (error.response?.status === 402) {
      if (typeof window !== "undefined") {
        // Dynamic import to avoid circular dep
        import("@/store/ui.store").then(({ useUiStore }) => {
          useUiStore.getState().openUpgradeModal(
            (error.response?.data as { code?: string })?.code
          );
        });
      }
    }

    return Promise.reject(error);
  }
);

async function _doRefresh(): Promise<string> {
  let refreshToken: string | null = null;
  try {
    const raw = localStorage.getItem("pigos-auth");
    if (raw) {
      const { state } = JSON.parse(raw) as { state: { refreshToken: string | null } };
      refreshToken = state?.refreshToken ?? null;
    }
  } catch {
    throw new Error("No refresh token");
  }

  if (!refreshToken) throw new Error("No refresh token");

  const { data } = await axios.post<{ access_token: string }>(
    `${API_BASE}/api/v1/auth/refresh`,
    { refresh_token: refreshToken }
  );

  // Update stored access token
  try {
    const raw = localStorage.getItem("pigos-auth");
    if (raw) {
      const parsed = JSON.parse(raw) as { state: Record<string, unknown> };
      parsed.state.accessToken = data.access_token;
      localStorage.setItem("pigos-auth", JSON.stringify(parsed));
    }
  } catch {
    // Ignore storage errors
  }

  return data.access_token;
}

function _clearAuth() {
  try {
    const raw = localStorage.getItem("pigos-auth");
    if (raw) {
      const parsed = JSON.parse(raw) as { state: Record<string, unknown> };
      parsed.state.accessToken = null;
      parsed.state.refreshToken = null;
      parsed.state.user = null;
      localStorage.setItem("pigos-auth", JSON.stringify(parsed));
    }
  } catch {
    localStorage.removeItem("pigos-auth");
  }
}

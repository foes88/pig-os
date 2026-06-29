import { apiClient } from "@/lib/api/client";
import type {
  LoginRequest,
  LoginResponse,
  MeResponse,
  OnboardingRequest,
  OnboardingResponse,
  RefreshResponse,
} from "@/types/api.types";

const BASE = "/api/v1/auth";

export const authApi = {
  login: (body: LoginRequest) =>
    apiClient.post<LoginResponse>(`${BASE}/login`, body).then((r) => r.data),

  me: () => apiClient.get<MeResponse>(`${BASE}/me`).then((r) => r.data),

  refresh: (refreshToken: string) =>
    apiClient
      .post<RefreshResponse>(`${BASE}/refresh`, { refresh_token: refreshToken })
      .then((r) => r.data),

  logout: () => apiClient.post(`${BASE}/logout`),

  onboard: (body: OnboardingRequest) =>
    apiClient.post<OnboardingResponse>("/api/v1/onboarding/complete", body).then((r) => r.data),
};

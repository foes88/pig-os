import { apiClient } from "@/lib/api/client";
import type {
  CountryConfig,
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

  // 공개 국가 설정 — 온보딩 드롭다운 + 국가별 프리필(통화/단위/타임존). 단일 소스 백엔드.
  countries: () =>
    apiClient.get<CountryConfig[]>("/api/v1/config/countries").then((r) => r.data),

  // 비밀번호 재설정 — 요청(이메일)·확정(토큰+새 비번). 백엔드는 열거방지로 항상 204.
  requestPasswordReset: (email: string) =>
    apiClient.post(`${BASE}/password-reset/request`, { email }),

  confirmPasswordReset: (token: string, newPassword: string) =>
    apiClient.post(`${BASE}/password-reset/confirm`, { token, new_password: newPassword }),
};

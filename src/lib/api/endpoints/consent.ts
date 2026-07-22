import { apiClient } from "@/lib/api/client";
import type {
  ConsentStatus, RecordConsentRequest, SignupPlan, WithdrawRequest,
} from "@/types/api.types";

// 동의 인프라 — 가입/설정 플랜 조회, 기록, 현재상태, 철회. (TERMS_DISPLAY §7)
export const consentApi = {
  signupPlan: (params: {
    selected_country: string; farm_country?: string; farm_state?: string;
    lang?: string; include_body?: boolean;
  }) => apiClient.get<SignupPlan>("/api/v1/consent/signup-plan", { params }).then((r) => r.data),

  record: (body: RecordConsentRequest) =>
    apiClient.post<ConsentStatus[]>("/api/v1/consent/record", body).then((r) => r.data),

  current: (farm_id?: string) =>
    apiClient.get<ConsentStatus[]>("/api/v1/consent/current", { params: farm_id ? { farm_id } : {} }).then((r) => r.data),

  withdraw: (body: WithdrawRequest) =>
    apiClient.post<ConsentStatus>("/api/v1/consent/withdraw", body).then((r) => r.data),
};

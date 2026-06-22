import { apiClient } from "@/lib/api/client";
import type { AdminOverview } from "@/types/api.types";

// 운영자 어드민 콘솔 API (SUPER_ADMIN 전용, 전사 스코프). 백엔드 /api/v1/admin/*.
const BASE = "/api/v1/admin";

export interface AdminMe {
  id: string;
  email: string;
  name: string;
  role: string;
}

export const adminApi = {
  overview: () => apiClient.get<AdminOverview>(`${BASE}/overview`).then((r) => r.data),
  me: () => apiClient.get<AdminMe>(`${BASE}/me`).then((r) => r.data),
};

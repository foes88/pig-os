import { apiClient } from "@/lib/api/client";
import type { KpiDashboard, KpiPolicy, KpiPresentation, KpiTrend } from "@/types/api.types";

const base = (farmId: string) => `/api/v1/farms/${farmId}/kpi`;

export const kpiApi = {
  dashboard: (farmId: string) =>
    apiClient.get<KpiDashboard>(`${base(farmId)}/dashboard`).then((r) => r.data),

  trend: (farmId: string, kpi: string, months = 6) =>
    apiClient
      .get<KpiTrend[]>(`${base(farmId)}/trend`, { params: { kpi, months } })
      .then((r) => r.data),

  // v0.4: 법역별 resolved KPI 정책(표시 대상). 대시보드/룰엔진 동적 구성용.
  policy: (farmId: string) =>
    apiClient.get<KpiPolicy[]>(`${base(farmId)}/policy`).then((r) => r.data),

  // 국가별 표현 정책 — 카드 순서·현지 명칭·headline. 정렬은 서버 확정.
  presentation: (farmId: string) =>
    apiClient.get<KpiPresentation>(`${base(farmId)}/presentation`).then((r) => r.data),
};

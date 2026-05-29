import { apiClient } from "@/lib/api/client";
import type { KpiDashboard, KpiTrend } from "@/types/api.types";

const base = (farmId: string) => `/api/v1/farms/${farmId}/kpi`;

export const kpiApi = {
  dashboard: (farmId: string) =>
    apiClient.get<KpiDashboard>(`${base(farmId)}/dashboard`).then((r) => r.data),

  trend: (farmId: string, kpi: string, months = 6) =>
    apiClient
      .get<KpiTrend[]>(`${base(farmId)}/trend`, { params: { kpi, months } })
      .then((r) => r.data),
};

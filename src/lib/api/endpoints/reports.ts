import { apiClient } from "@/lib/api/client";
import type { GrowFinishRow, ReproductionRow, SowHistoryCycle } from "@/types/api.types";

const base = (farmId: string) => `/api/v1/farms/${farmId}/reports`;

export const reportsApi = {
  reproduction: (farmId: string, startDate: string, endDate: string, period = "monthly") =>
    apiClient
      .get<ReproductionRow[]>(`${base(farmId)}/reproduction`, {
        params: { start_date: startDate, end_date: endDate, period },
      })
      .then((r) => r.data),

  growFinish: (farmId: string, startDate: string, endDate: string) =>
    apiClient
      .get<GrowFinishRow[]>(`${base(farmId)}/grow-finish`, {
        params: { start_date: startDate, end_date: endDate },
      })
      .then((r) => r.data),

  sowHistory: (farmId: string, sowId: string) =>
    apiClient.get<SowHistoryCycle[]>(`${base(farmId)}/sows/${sowId}/history`).then((r) => r.data),
};

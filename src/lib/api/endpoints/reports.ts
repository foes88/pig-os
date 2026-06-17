import { apiClient } from "@/lib/api/client";
import type {
  GrowFinishRow,
  ProductionSummary,
  ReproductionRow,
  SowHistoryCycle,
} from "@/types/api.types";

const base = (farmId: string) => `/api/v1/farms/${farmId}/reports`;

export const reportsApi = {
  reproduction: (
    farmId: string,
    startDate: string,
    endDate: string,
    period = "monthly",
    groupBy = "period",
  ) =>
    apiClient
      .get<ReproductionRow[]>(`${base(farmId)}/reproduction`, {
        params: { start_date: startDate, end_date: endDate, period, group_by: groupBy },
      })
      .then((r) => r.data),

  productionSummary: (
    farmId: string,
    startDate: string,
    endDate: string,
    period = "monthly",
    groupBy = "period",
  ) =>
    apiClient
      .get<ProductionSummary>(`${base(farmId)}/production-summary`, {
        params: { start_date: startDate, end_date: endDate, period, group_by: groupBy },
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

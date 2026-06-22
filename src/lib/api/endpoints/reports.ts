import { apiClient } from "@/lib/api/client";
import type {
  ComprehensiveDailyReport,
  DailyReport,
  DataQualityIssue,
  FarrowingPerfRow,
  GrowFinishRow,
  MortalityReport,
  ProductionSummary,
  ReproductionRow,
  SowHistoryCycle,
  SowStatusReport,
} from "@/types/api.types";

const base = (farmId: string) => `/api/v1/farms/${farmId}/reports`;

export const reportsApi = {
  daily: (farmId: string, date: string) =>
    apiClient.get<DailyReport>(`${base(farmId)}/daily`, { params: { date } }).then((r) => r.data),

  comprehensiveDaily: (farmId: string, date: string) =>
    apiClient.get<ComprehensiveDailyReport>(`${base(farmId)}/comprehensive-daily`, { params: { date } }).then((r) => r.data),

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

  dataQuality: (farmId: string) =>
    apiClient.get<DataQualityIssue[]>(`${base(farmId)}/data-quality`).then((r) => r.data),

  sowStatus: (farmId: string) =>
    apiClient.get<SowStatusReport>(`${base(farmId)}/sow-status`).then((r) => r.data),

  farrowing: (farmId: string, startDate: string, endDate: string) =>
    apiClient
      .get<FarrowingPerfRow[]>(`${base(farmId)}/farrowing`, {
        params: { start_date: startDate, end_date: endDate },
      })
      .then((r) => r.data),

  mortality: (farmId: string, startDate: string, endDate: string) =>
    apiClient
      .get<MortalityReport>(`${base(farmId)}/mortality`, {
        params: { start_date: startDate, end_date: endDate },
      })
      .then((r) => r.data),
};

import { apiClient } from "@/lib/api/client";
import type { CullCandidate, OverdueSummary } from "@/types/api.types";

const base = (farmId: string) => `/api/v1/farms/${farmId}/alerts`;

export const alertsApi = {
  overdue: (farmId: string) =>
    apiClient.get<OverdueSummary>(`${base(farmId)}/overdue`).then((r) => r.data),

  cullCandidates: (farmId: string) =>
    apiClient.get<CullCandidate[]>(`${base(farmId)}/cull-candidates`).then((r) => r.data),
};

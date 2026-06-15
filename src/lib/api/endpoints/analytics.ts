import { apiClient } from "@/lib/api/client";
import type { PrrsByGeneticsResponse } from "@/types/api.types";

export const analyticsApi = {
  prrsByGenetics: (farmId: string) =>
    apiClient
      .get<PrrsByGeneticsResponse>(`/api/v1/farms/${farmId}/analytics/prrs-by-genetics`)
      .then((r) => r.data),
};

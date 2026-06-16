import { apiClient } from "@/lib/api/client";
import type { ThresholdOverrideRequest, ThresholdRow } from "@/types/api.types";

const base = (farmId: string) => `/api/v1/farms/${farmId}/thresholds`;

export const thresholdsApi = {
  list: (farmId: string) =>
    apiClient.get<ThresholdRow[]>(base(farmId)).then((r) => r.data),

  setOverride: (farmId: string, metricCode: string, body: ThresholdOverrideRequest) =>
    apiClient.patch<ThresholdRow>(`${base(farmId)}/${metricCode}`, body).then((r) => r.data),

  clearOverride: (farmId: string, metricCode: string) =>
    apiClient.delete(`${base(farmId)}/${metricCode}`).then(() => undefined),
};

import { apiClient } from "@/lib/api/client";
import type { EventDefinition, Farm, FarmLocalConfig } from "@/types/api.types";

const BASE = "/api/v1/farms";

export const farmsApi = {
  list: () =>
    apiClient.get<Farm[]>(BASE).then((r) => r.data),

  get: (farmId: string) =>
    apiClient.get<Farm>(`${BASE}/${farmId}`).then((r) => r.data),

  getLocalConfig: (farmId: string) =>
    apiClient.get<FarmLocalConfig>(`${BASE}/${farmId}/config`).then((r) => r.data),

  getEventDefinitions: (farmId: string) =>
    apiClient.get<EventDefinition[]>(`${BASE}/${farmId}/events/definitions`).then((r) => r.data),
};

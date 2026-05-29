import { apiClient } from "@/lib/api/client";
import type { Farm } from "@/types/api.types";

const BASE = "/api/v1/farms";

export const farmsApi = {
  list: () =>
    apiClient.get<Farm[]>(BASE).then((r) => r.data),

  get: (farmId: string) =>
    apiClient.get<Farm>(`${BASE}/${farmId}`).then((r) => r.data),
};

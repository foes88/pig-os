import { apiClient } from "@/lib/api/client";
import type { SyncRequest, SyncResponse } from "@/types/api.types";

export const syncApi = {
  sync: (farmId: string, body: SyncRequest) =>
    apiClient
      .post<SyncResponse>(`/api/v1/farms/${farmId}/sync`, body)
      .then((r) => r.data),
};

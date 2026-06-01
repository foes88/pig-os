import { apiClient } from "@/lib/api/client";
import type {
  CreateFinisherGroupRequest,
  FinisherGroup,
  FinisherGroupShipRequest,
} from "@/types/api.types";

const base = (farmId: string) => `/api/v1/farms/${farmId}/finishers`;

export const finishersApi = {
  list: (farmId: string, activeOnly = false) =>
    apiClient
      .get<FinisherGroup[]>(base(farmId), { params: { active_only: activeOnly } })
      .then((r) => r.data),

  create: (farmId: string, body: CreateFinisherGroupRequest) =>
    apiClient.post<FinisherGroup>(base(farmId), body).then((r) => r.data),

  ship: (farmId: string, groupId: string, body: FinisherGroupShipRequest) =>
    apiClient
      .post<FinisherGroup>(`${base(farmId)}/${groupId}/ship`, body)
      .then((r) => r.data),

  delete: (farmId: string, groupId: string) =>
    apiClient.delete(`${base(farmId)}/${groupId}`),
};

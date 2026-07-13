import { apiClient } from "@/lib/api/client";
import type {
  CreateFinisherGroupRequest,
  FinisherGroup,
  FinisherGroupShipRequest,
  UpdateFinisherGroupRequest,
} from "@/types/api.types";

const base = (farmId: string) => `/api/v1/farms/${farmId}/finishers`;

export const finishersApi = {
  // limit=200(엔드포인트 최대) — 미지정 시 기본 50으로 잘려 클라 페이지네이션이 초과분을 조용히 유실하던 버그 방지.
  list: (farmId: string, activeOnly = false) =>
    apiClient
      .get<FinisherGroup[]>(base(farmId), { params: { active_only: activeOnly, limit: 200 } })
      .then((r) => r.data),

  create: (farmId: string, body: CreateFinisherGroupRequest) =>
    apiClient.post<FinisherGroup>(base(farmId), body).then((r) => r.data),

  ship: (farmId: string, groupId: string, body: FinisherGroupShipRequest) =>
    apiClient
      .post<FinisherGroup>(`${base(farmId)}/${groupId}/ship`, body)
      .then((r) => r.data),

  update: (farmId: string, groupId: string, body: UpdateFinisherGroupRequest) =>
    apiClient.patch<FinisherGroup>(`${base(farmId)}/${groupId}`, body).then((r) => r.data),

  delete: (farmId: string, groupId: string) =>
    apiClient.delete(`${base(farmId)}/${groupId}`),
};

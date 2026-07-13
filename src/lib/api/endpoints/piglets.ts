import { apiClient } from "@/lib/api/client";
import type {
  CreatePigletGroupRequest,
  CreatePigletTransferRequest,
  PigletGroup,
  PigletGroupTransferOutRequest,
  PigletTransfer,
} from "@/types/api.types";

const base = (farmId: string) => `/api/v1/farms/${farmId}/piglets`;

export const pigletsApi = {
  list: (farmId: string, activeOnly = false) =>
    apiClient
      // limit=200(엔드포인트 최대) — 기본 50 초과분이 조용히 유실되던 버그 방지(자돈그룹 목록 페이지네이션 UI 없음).
      .get<PigletGroup[]>(base(farmId), { params: { active_only: activeOnly, limit: 200 } })
      .then((r) => r.data),

  create: (farmId: string, body: CreatePigletGroupRequest) =>
    apiClient.post<PigletGroup>(base(farmId), body).then((r) => r.data),

  recordDeath: (farmId: string, groupId: string, count: number, notes?: string) =>
    apiClient
      .post<PigletGroup>(`${base(farmId)}/${groupId}/deaths`, { head_count_dead: count, notes })
      .then((r) => r.data),

  transferOut: (farmId: string, groupId: string, body: PigletGroupTransferOutRequest) =>
    apiClient
      .post<PigletGroup>(`${base(farmId)}/${groupId}/transfer`, body)
      .then((r) => r.data),

  createTransfer: (farmId: string, body: CreatePigletTransferRequest) =>
    apiClient.post<PigletTransfer>(`${base(farmId)}/transfers`, body).then((r) => r.data),

  listTransfers: (farmId: string, sowId?: string) =>
    apiClient
      .get<PigletTransfer[]>(`${base(farmId)}/transfers`, { params: { sow_id: sowId } })
      .then((r) => r.data),
};

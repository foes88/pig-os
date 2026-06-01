import { apiClient } from "@/lib/api/client";
import type {
  CreateSowRequest,
  PagedResult,
  Sow,
  SowCullRequest,
  SowStatus,
  UpdateSowRequest,
} from "@/types/api.types";

const base = (farmId: string) => `/api/v1/farms/${farmId}/sows`;

export interface ListSowsParams {
  status?: SowStatus;
  page?: number;
  per_page?: number;
  search?: string;
}

export const sowsApi = {
  list: (farmId: string, params?: ListSowsParams) =>
    apiClient
      .get<PagedResult<Sow>>(base(farmId), { params })
      .then((r) => r.data),

  get: (farmId: string, sowId: string) =>
    apiClient.get<Sow>(`${base(farmId)}/${sowId}`).then((r) => r.data),

  create: (farmId: string, body: CreateSowRequest) =>
    apiClient.post<Sow>(base(farmId), body).then((r) => r.data),

  update: (farmId: string, sowId: string, body: UpdateSowRequest) =>
    apiClient.patch<Sow>(`${base(farmId)}/${sowId}`, body).then((r) => r.data),

  delete: (farmId: string, sowId: string) =>
    apiClient.delete(`${base(farmId)}/${sowId}`),

  cull: (farmId: string, sowId: string, body: SowCullRequest) =>
    apiClient.post<Sow>(`${base(farmId)}/${sowId}/cull`, body).then((r) => r.data),
};

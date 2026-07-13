import { apiClient } from "@/lib/api/client";

export interface Boar {
  id: string;
  farm_id: string;
  ear_tag: string;
  breed?: string;
  breed_company?: string;
  status: "ACTIVE" | "CULLED" | "DEAD" | "TRANSFERRED";
  entry_date: string;
  entry_type?: string;
  semen_quality?: string;
  created_at: string;
}

export interface CreateBoarRequest {
  ear_tag: string;
  breed?: string;
  breed_company?: string;
  entry_date: string;
  entry_type?: string;
  semen_quality?: string;
}

export interface UpdateBoarRequest {
  ear_tag?: string;
  breed?: string;
  breed_company?: string;
  status?: Boar["status"];
  semen_quality?: string;
}

const base = (farmId: string) => `/api/v1/farms/${farmId}/boars`;

export const boarsApi = {
  list: (farmId: string, status?: string) =>
    apiClient
      // limit=500(엔드포인트 최대) — 기본 100 초과분이 조용히 유실되던 버그 방지.
      .get<Boar[]>(base(farmId), { params: { status, limit: 500 } })
      .then((r) => r.data),

  get: (farmId: string, boarId: string) =>
    apiClient.get<Boar>(`${base(farmId)}/${boarId}`).then((r) => r.data),

  create: (farmId: string, body: CreateBoarRequest) =>
    apiClient.post<Boar>(base(farmId), body).then((r) => r.data),

  update: (farmId: string, boarId: string, body: UpdateBoarRequest) =>
    apiClient.patch<Boar>(`${base(farmId)}/${boarId}`, body).then((r) => r.data),
};

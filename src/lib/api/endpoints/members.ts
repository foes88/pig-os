import { apiClient } from "@/lib/api/client";
import type { FarmRole } from "@/types/api.types";

export type { FarmRole };

export interface Member {
  user_id: string;
  name: string;
  email: string | null;
  role: FarmRole;
  active: boolean;
}

export interface CreateMemberRequest {
  name: string;
  username: string;
  email: string;
  password: string;
  role: FarmRole;
}

export interface UpdateMemberRequest {
  role?: FarmRole;
  active?: boolean;
}

const base = (farmId: string) => `/api/v1/farms/${farmId}/members`;

export const membersApi = {
  list: (farmId: string) =>
    apiClient.get<Member[]>(base(farmId)).then((r) => r.data),

  create: (farmId: string, body: CreateMemberRequest) =>
    apiClient.post<Member>(base(farmId), body).then((r) => r.data),

  update: (farmId: string, userId: string, body: UpdateMemberRequest) =>
    apiClient.patch<Member>(`${base(farmId)}/${userId}`, body).then((r) => r.data),
};

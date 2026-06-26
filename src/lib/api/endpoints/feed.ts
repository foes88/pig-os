import { apiClient } from "@/lib/api/client";

export interface FeedRecord {
  id: string;
  farm_id: string;
  record_date: string;
  quantity_kg: number;
  feed_type: string | null;
  sow_id: string | null;
  group_id: string | null;
  building_id: string | null;
  unit_cost: number | null;
  currency: string | null;
  notes: string | null;
  created_at: string;
}

export interface CreateFeedRecordRequest {
  record_date: string;
  quantity_kg: number;
  feed_type?: string | null;
  group_id?: string | null;
  building_id?: string | null;
  notes?: string | null;
}

const base = (farmId: string) => `/api/v1/farms/${farmId}/feed-records`;

export const feedApi = {
  list: (farmId: string) =>
    apiClient.get<FeedRecord[]>(base(farmId)).then((r) => r.data),
  create: (farmId: string, body: CreateFeedRecordRequest) =>
    apiClient.post<FeedRecord>(base(farmId), body).then((r) => r.data),
  delete: (farmId: string, id: string) =>
    apiClient.delete(`${base(farmId)}/${id}`),
};

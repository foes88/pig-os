import { apiClient } from "@/lib/api/client";
import type { ChatQuery, ChatResponse } from "@/types/api.types";

export const chatApi = {
  query: (farmId: string, body: ChatQuery) =>
    apiClient
      .post<ChatResponse>(`/api/v1/farms/${farmId}/chat/query`, body)
      .then((r) => r.data),
};

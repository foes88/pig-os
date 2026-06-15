import { apiClient } from "@/lib/api/client";
import type { MarkReadResult, NotificationListResponse } from "@/types/api.types";

export interface ListNotificationsParams {
  farmId?: string;
  unreadOnly?: boolean;
  limit?: number;
  offset?: number;
}

export const notificationsApi = {
  list: (params: ListNotificationsParams = {}) => {
    const q = new URLSearchParams();
    if (params.farmId) q.set("farm_id", params.farmId);
    if (params.unreadOnly) q.set("unread_only", "true");
    if (params.limit != null) q.set("limit", String(params.limit));
    if (params.offset != null) q.set("offset", String(params.offset));
    const qs = q.toString();
    return apiClient
      .get<NotificationListResponse>(`/api/v1/notifications${qs ? `?${qs}` : ""}`)
      .then((r) => r.data);
  },

  markRead: (notificationId: string) =>
    apiClient
      .patch<MarkReadResult>(`/api/v1/notifications/${notificationId}/read`)
      .then((r) => r.data),

  markAllRead: (farmId?: string) =>
    apiClient
      .post<MarkReadResult>(`/api/v1/notifications/read-all${farmId ? `?farm_id=${farmId}` : ""}`)
      .then((r) => r.data),
};

import { apiClient } from "@/lib/api/client";
import type { AnnouncementOut, SupportTicketDetail, SupportTicketOut } from "@/types/api.types";

// 고객(로그인 사용자)용 공지 읽기 + 1:1 문의.
export const contentApi = {
  announcements: (lang?: string) =>
    apiClient.get<AnnouncementOut[]>("/api/v1/announcements", { params: lang ? { lang } : {} }).then((r) => r.data),

  myTickets: () => apiClient.get<SupportTicketOut[]>("/api/v1/support/tickets").then((r) => r.data),
  ticket: (id: string) => apiClient.get<SupportTicketDetail>(`/api/v1/support/tickets/${id}`).then((r) => r.data),
  createTicket: (body: { subject: string; body: string; farm_id?: string }) =>
    apiClient.post<SupportTicketOut>("/api/v1/support/tickets", body).then((r) => r.data),
  followup: (id: string, bodyText: string) =>
    apiClient.post<SupportTicketDetail>(`/api/v1/support/tickets/${id}/reply`, { body: bodyText }).then((r) => r.data),
};

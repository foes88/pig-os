import { apiClient } from "@/lib/api/client";
import type {
  AdminMemberDetail,
  AdminMemberRow,
  AdminOverview,
  AdminPaged,
  AnnouncementOut,
  PilotSignupRow,
  SupportTicketDetail,
  SupportTicketOut,
} from "@/types/api.types";

export interface AnnouncementInput {
  title: string;
  body: string;
  category?: string;
  pinned?: boolean;
  published?: boolean;
  publish_from?: string | null;
  publish_until?: string | null;
  lang?: string | null;
}

// 운영자 어드민 콘솔 API (SUPER_ADMIN 전용, 전사 스코프). 백엔드 /api/v1/admin/*.
const BASE = "/api/v1/admin";

export interface AdminMe {
  id: string;
  email: string;
  name: string;
  role: string;
}

export interface MemberQuery {
  q?: string;
  status?: string;
  org_id?: string;
  page?: number;
  per_page?: number;
}

export const adminApi = {
  overview: () => apiClient.get<AdminOverview>(`${BASE}/overview`).then((r) => r.data),
  me: () => apiClient.get<AdminMe>(`${BASE}/me`).then((r) => r.data),

  // 회원
  members: (params: MemberQuery = {}) =>
    apiClient.get<AdminPaged<AdminMemberRow>>(`${BASE}/members`, { params }).then((r) => r.data),
  member: (id: string) =>
    apiClient.get<AdminMemberDetail>(`${BASE}/members/${id}`).then((r) => r.data),
  updateMemberStatus: (id: string, body: { approval_status?: string; active?: boolean }) =>
    apiClient.patch<AdminMemberRow>(`${BASE}/members/${id}/status`, body).then((r) => r.data),

  // 베타 가입
  pilotSignups: (params: { status?: string; page?: number; per_page?: number } = {}) =>
    apiClient.get<AdminPaged<PilotSignupRow>>(`${BASE}/pilot-signups`, { params }).then((r) => r.data),
  approvePilot: (id: string, body: { initial_password: string; system_role?: string }) =>
    apiClient
      .post<{ user_id: string; email: string; initial_password: string; note: string }>(
        `${BASE}/pilot-signups/${id}/approve`,
        body,
      )
      .then((r) => r.data),

  // 공지
  announcements: () => apiClient.get<AnnouncementOut[]>(`${BASE}/announcements`).then((r) => r.data),
  createAnnouncement: (body: AnnouncementInput) =>
    apiClient.post<AnnouncementOut>(`${BASE}/announcements`, body).then((r) => r.data),
  updateAnnouncement: (id: string, body: Partial<AnnouncementInput>) =>
    apiClient.put<AnnouncementOut>(`${BASE}/announcements/${id}`, body).then((r) => r.data),
  deleteAnnouncement: (id: string) =>
    apiClient.delete(`${BASE}/announcements/${id}`).then((r) => r.data),

  // 문의
  tickets: (params: { status?: string; page?: number; per_page?: number } = {}) =>
    apiClient.get<AdminPaged<SupportTicketOut>>(`${BASE}/support`, { params }).then((r) => r.data),
  ticket: (id: string) =>
    apiClient.get<SupportTicketDetail>(`${BASE}/support/${id}`).then((r) => r.data),
  replyTicket: (id: string, bodyText: string) =>
    apiClient.post<SupportTicketDetail>(`${BASE}/support/${id}/reply`, { body: bodyText }).then((r) => r.data),
};

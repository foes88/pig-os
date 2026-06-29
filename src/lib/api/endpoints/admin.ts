import { apiClient } from "@/lib/api/client";
import type {
  AdminMemberDetail,
  AdminMemberRow,
  AdminOverview,
  AdminPaged,
  AdminOrgFarm,
  AdminOrgRow,
  AdminRuleRow,
  AnnouncementOut,
  AuditRow,
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

  // AI 규칙
  rules: () => apiClient.get<AdminRuleRow[]>(`${BASE}/rules`).then((r) => r.data),
  updateRule: (ruleId: string, body: { enabled?: boolean; warning?: number | null; critical?: number | null }) =>
    apiClient.patch<AdminRuleRow>(`${BASE}/rules/${ruleId}`, body).then((r) => r.data),

  // 활동 로그
  auditLog: (params: { action?: string; entity_type?: string; page?: number; per_page?: number } = {}) =>
    apiClient.get<AdminPaged<AuditRow>>(`${BASE}/audit-log`, { params }).then((r) => r.data),

  // 조직 트리 (업체→총판→대리점→농장)
  orgs: () => apiClient.get<AdminOrgRow[]>(`${BASE}/orgs`).then((r) => r.data),
  orgFarms: (orgId: string) => apiClient.get<AdminOrgFarm[]>(`${BASE}/orgs/${orgId}/farms`).then((r) => r.data),
  createOrg: (body: { name: string; org_type: string; parent_org_id?: string | null; country: string }) =>
    apiClient.post<AdminOrgRow>(`${BASE}/orgs`, body).then((r) => r.data),
  updateOrg: (orgId: string, body: { name?: string; org_type?: string; parent_org_id?: string | null }) =>
    apiClient.patch<AdminOrgRow>(`${BASE}/orgs/${orgId}`, body).then((r) => r.data),
  reassignFarm: (farmId: string, orgId: string) =>
    apiClient.patch<AdminOrgFarm>(`${BASE}/farms/${farmId}/org`, { org_id: orgId }).then((r) => r.data),

  // 코드/마스터 데이터 CRUD (G4): kind = diseases|vaccines|medications|event-definitions
  masterList: (kind: string) =>
    apiClient.get<Record<string, unknown>[]>(`${BASE}/master/${kind}`).then((r) => r.data),
  masterCreate: (kind: string, body: Record<string, unknown>) =>
    apiClient.post<Record<string, unknown>>(`${BASE}/master/${kind}`, body).then((r) => r.data),
  masterUpdate: (kind: string, pk: string, body: Record<string, unknown>) =>
    apiClient.patch<Record<string, unknown>>(`${BASE}/master/${kind}/${encodeURIComponent(pk)}`, body).then((r) => r.data),
  masterDelete: (kind: string, pk: string) =>
    apiClient.delete(`${BASE}/master/${kind}/${encodeURIComponent(pk)}`).then((r) => r.data),
};

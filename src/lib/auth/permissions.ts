// 역할별 클라이언트 권한 게이팅 (백엔드 require_farm_role과 일치).
// canEntry: OWNER/MANAGER/WORKER(입력) · canManage: OWNER/MANAGER(운영관리) · canOwn: OWNER만(소유자 전용).
// 소유자 전용 = 멤버 임명/역할변경 · 과금/구독 · 계정/농장 삭제. VIEWER/VET = 읽기전용.

const ENTRY = new Set([
  "FARM_OWNER", "FARM_MANAGER", "FARM_WORKER", "OWNER", "MANAGER", "WORKER", "SUPER_ADMIN",
]);
const MANAGE = new Set([
  "FARM_OWNER", "FARM_MANAGER", "OWNER", "MANAGER", "SUPER_ADMIN",
]);
const OWN = new Set([
  "FARM_OWNER", "OWNER", "SUPER_ADMIN",
]);

export function canEntry(role?: string | null): boolean {
  return !!role && ENTRY.has(role);
}

export function canManage(role?: string | null): boolean {
  return !!role && MANAGE.has(role);
}

/** 소유자 전용 권한 — 멤버 임명·과금·삭제. MANAGER는 false. */
export function canOwn(role?: string | null): boolean {
  return !!role && OWN.has(role);
}

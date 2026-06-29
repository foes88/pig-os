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

/**
 * 활성 농장 기준 유효 role. 멀티팜에서 농장마다 역할이 다를 수 있으므로
 * farm_roles[activeFarmId]를 우선 사용하고, 없으면 전역 role로 폴백
 * (SUPER_ADMIN·단일농장 사용자 등은 farm_roles가 비어 전역 role 사용).
 * 백엔드 effective_farm_role과 동일 의미.
 */
export function effectiveRole(
  user: { role?: string | null; farm_roles?: Record<string, string> } | null | undefined,
  activeFarmId: string | null | undefined,
): string | null {
  if (!user) return null;
  if (activeFarmId && user.farm_roles && user.farm_roles[activeFarmId]) {
    return user.farm_roles[activeFarmId];
  }
  return user.role ?? null;
}

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

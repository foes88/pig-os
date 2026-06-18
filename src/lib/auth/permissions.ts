// 역할별 클라이언트 권한 게이팅 (백엔드 require_farm_role과 일치).
// 입력(canEntry): OWNER/MANAGER/WORKER, 관리(canManage): OWNER/MANAGER. VIEWER/VET = 읽기전용.

const ENTRY = new Set([
  "FARM_OWNER", "FARM_MANAGER", "FARM_WORKER", "OWNER", "MANAGER", "WORKER", "SUPER_ADMIN",
]);
const MANAGE = new Set([
  "FARM_OWNER", "FARM_MANAGER", "OWNER", "MANAGER", "SUPER_ADMIN",
]);

export function canEntry(role?: string | null): boolean {
  return !!role && ENTRY.has(role);
}

export function canManage(role?: string | null): boolean {
  return !!role && MANAGE.has(role);
}

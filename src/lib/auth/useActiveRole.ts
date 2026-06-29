"use client";

import { useAuthStore } from "@/store/auth.store";
import { effectiveRole } from "@/lib/auth/permissions";

/**
 * 현재 활성 농장 기준 사용자 역할.
 * 게이팅(canEntry/canManage/canOwn)은 전역 user.role 대신 이 값을 써야
 * 멀티팜에서 농장별 권한이 백엔드(require_farm_role)와 일치한다.
 */
export function useActiveRole(): string | null {
  const user = useAuthStore((s) => s.user);
  const activeFarmId = useAuthStore((s) => s.activeFarmId);
  return effectiveRole(user, activeFarmId);
}

// 8개 로케일 — 공개 7개(en/zh/es/vi/th/pt/ru) + 한국어(ko, 플랫폼 관리자 전용).
export const locales = ["en", "ko", "zh", "es", "vi", "th", "pt", "ru"] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = "en";

// 한국어는 플랫폼 관리자 전용 — 해외 출시: 일반/고객 계정과 로그인 전 화면엔 숨김.
// (관리자 본인이 한국인이라 한국어 확인 필요 → admin 로그인 후에만 노출)
export const ADMIN_ONLY_LOCALES: readonly Locale[] = ["ko"];

const PLATFORM_ADMIN_ROLES = new Set([
  "SUPER_ADMIN",
  "VENDOR_ADMIN",
  "DISTRIBUTOR_ADMIN",
  "DEALER_ADMIN",
]);

/** OrgRole(플랫폼 관리자) 여부. FARM_OWNER 등 농장 역할은 false(해외 고객과 동일). */
export function isPlatformAdmin(role?: string | null): boolean {
  return !!role && PLATFORM_ADMIN_ROLES.has(role);
}

/** 역할에 따라 선택 가능한 로케일 목록. 비관리자는 ko 제외. */
export function visibleLocales(role?: string | null): Locale[] {
  if (isPlatformAdmin(role)) return [...locales];
  return locales.filter((l) => !ADMIN_ONLY_LOCALES.includes(l));
}

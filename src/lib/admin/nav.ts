import {
  LayoutDashboard,
  Users,
  Megaphone,
  LifeBuoy,
  SlidersHorizontal,
  type LucideIcon,
} from "lucide-react";

// 운영자 어드민 메뉴 — 단일 선언적 레지스트리. 메뉴 확장 = 여기 항목 추가만.
// (하드코딩 분산 방지. 추후 DB-driven 으로 확장 가능하도록 데이터 형태 유지.)
export interface AdminNavItem {
  href: string;
  /** admin i18n 네임스페이스의 라벨 키 */
  labelKey: string;
  icon: LucideIcon;
  /** "ready"=구현됨, "soon"=준비중(클릭 가능하나 빈 상태) */
  status: "ready" | "soon";
}

export const ADMIN_NAV: AdminNavItem[] = [
  { href: "/admin", labelKey: "navOverview", icon: LayoutDashboard, status: "ready" },
  { href: "/admin/users", labelKey: "navMembers", icon: Users, status: "ready" },
  { href: "/admin/announcements", labelKey: "navAnnouncements", icon: Megaphone, status: "ready" },
  { href: "/admin/support", labelKey: "navSupport", icon: LifeBuoy, status: "ready" },
  { href: "/admin/rules", labelKey: "navRules", icon: SlidersHorizontal, status: "ready" },
];

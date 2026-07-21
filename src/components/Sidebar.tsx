"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  AlertTriangle,
  LayoutDashboard,
  PiggyBank,
  Heart,
  ClipboardList,
  BarChart3,
  FileText,
  MessageSquareText,
  Layers,
  Store,
  Settings,
  ChevronLeft,
  ChevronRight,
  Beef,
  ListTodo,
  Dna,
  ShieldCheck,
  Baby,
  TrendingDown,
  Wheat,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useAuthStore } from "@/store/auth.store";
import { alertsApi } from "@/lib/api/endpoints/alerts";
import { notificationsApi } from "@/lib/api/endpoints/notifications";
import { queryKeys } from "@/lib/api/queryKeys";
import type { Locale } from "@/i18n/config";

// 라벨은 messages/*.json 의 sidebar 네임스페이스(파일 단일소스, 인라인 제거).
interface NavItem {
  href: string;
  icon: React.ElementType;
  k: string;            // sidebar 네임스페이스 키
  badge?: "alerts"; // 통합 알림 배지(관리대상+미읽음 합산)
}

// 메뉴 재설계 2026-06 (docs/menu-redesign-2026-06.md): PigPlan식 그룹 재편 + 알림 통합 + 분만사 제거
const NAV_GROUPS: { labelKey?: string; items: NavItem[] }[] = [
  {
    items: [
      { href: "/", icon: LayoutDashboard, k: "dashboard" },
    ],
  },
  {
    items: [
      { href: "/record", icon: ClipboardList, k: "record" },
    ],
  },
  {
    labelKey: "grpHerd",
    items: [
      { href: "/sows",      icon: PiggyBank, k: "sows" },
      { href: "/boars",     icon: Heart,     k: "boars" },
      { href: "/piglets",   icon: Layers,    k: "piglets" },
      { href: "/finishers", icon: Beef,      k: "finishers" },
      { href: "/feed",      icon: Wheat,     k: "feed" },
    ],
  },
  {
    labelKey: "grpTasks",
    items: [
      { href: "/tasks",  icon: ListTodo,       k: "tasks" },
      { href: "/alerts", icon: AlertTriangle, badge: "alerts", k: "alerts" },
    ],
  },
  {
    labelKey: "grpReports",
    items: [
      { href: "/kpi",                  icon: BarChart3, k: "kpi" },
      { href: "/reports/sow-status",   icon: PiggyBank, k: "sowStatusMenu" },
      { href: "/reports/daily",        icon: FileText,  k: "dailyReport" },
      { href: "/reports/comprehensive-daily", icon: FileText, k: "dailyFull" },
      { href: "/reports/farrowing",    icon: Baby,      k: "farrowWean" },
      { href: "/reports/mortality",    icon: TrendingDown, k: "mortality" },
      { href: "/reports/reproduction", icon: FileText,  k: "production" },
      { href: "/reports/grow-finish",  icon: Beef,      k: "growFinish" },
      { href: "/reports",              icon: FileText,  k: "sowReport" },
      { href: "/reports/ledger",       icon: ClipboardList, k: "ledger" },
      { href: "/reports/prrs",         icon: Dna,       k: "prrs" },
      { href: "/reports/data-quality", icon: ShieldCheck, k: "dataQuality" },
    ],
  },
  {
    labelKey: "grpAddons",
    items: [
      { href: "/addons", icon: Store, k: "addonStore" },
    ],
  },
];

const BOTTOM_ITEMS: NavItem[] = [
  { href: "/settings", icon: Settings, k: "settings" },
];

interface SidebarProps {
  lang?: Locale;
  collapsed?: boolean;
  onCollapse?: () => void;
  onAskAI?: () => void;
}

export function Sidebar({ collapsed = false, onCollapse, onAskAI }: SidebarProps) {
  const pathname = usePathname();
  const t = useTranslations("sidebar");
  const user = useAuthStore((s) => s.user);
  const w = collapsed ? 64 : 224;
  const farmId = useAuthStore((s) => s.activeFarmId);
  const { data: overdue } = useQuery({
    queryKey: queryKeys.alerts.overdue(farmId ?? ""),
    queryFn: () => alertsApi.overdue(farmId!),
    enabled: !!farmId,
    refetchInterval: 5 * 60 * 1000,
  });
  const alertCount = overdue?.total ?? 0;
  const { data: notifUnread } = useQuery({
    queryKey: queryKeys.notifications.unread(farmId ?? ""),
    queryFn: () => notificationsApi.list({ farmId: farmId!, limit: 0 }),
    enabled: !!farmId,
    refetchInterval: 5 * 60 * 1000,
  });
  const unreadCount = notifUnread?.unread_count ?? 0;

  // active 항목 = 현재 경로에 매칭되는 href 중 "가장 긴(가장 구체적인)" 하나만.
  // (예: /reports/reproduction → '생산성적'만 active, 상위 '/reports'(모돈보고서)는 비활성)
  const allHrefs = [
    ...NAV_GROUPS.flatMap((g) => g.items.map((i) => i.href)),
    ...BOTTOM_ITEMS.map((i) => i.href),
  ];
  const activeHref = allHrefs
    .filter((h) => (h === "/" ? pathname === "/" : pathname === h || pathname?.startsWith(h + "/")))
    .sort((a, b) => b.length - a.length)[0];

  return (
    <aside
      data-testid="sidebar"
      style={{ width: w }}
      className="hidden md:flex fixed top-0 left-0 h-screen bg-console border-r border-console-line flex-col z-50 transition-all duration-200 overflow-hidden"
    >
      {/* Logo — green mark + PigOS (Operational Console) */}
      <div className="flex items-center gap-2.5 px-4 py-4 border-b border-console-line flex-shrink-0">
        <Link href="/" className="flex items-center flex-1 min-w-0">
          {/* 공식 PigOS 로고 — 펼침: 가로형(심볼+워드마크), 접힘: 심볼만. 초록 사각형 제거 */}
          <Image
            src={collapsed ? "/logos/pigos-symbol-dark.svg" : "/logos/pigos-logo-horizontal-dark.svg"}
            alt="PigOS"
            width={collapsed ? 28 : 74}
            height={28}
            className={collapsed ? "w-[28px] h-[28px]" : "h-[26px] w-auto"}
            priority
          />
        </Link>
        {!collapsed && (
          <span className="ml-auto text-[9.5px] font-mono text-console-mut border border-console-line px-1.5 py-0.5 rounded">
            v4
          </span>
        )}
        <button
          onClick={onCollapse}
          className="p-1 rounded-md text-console-mut hover:text-console-text hover:bg-console2 transition flex-shrink-0"
          title={collapsed ? "Expand" : "Collapse"}
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>

      {/* Farm switcher */}
      {!collapsed && (
        <div className="px-3 pt-3 pb-1.5">
          <div className="bg-console2 rounded-[9px] px-3 py-2.5 flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-md bg-brand text-white flex items-center justify-center text-[11px] font-bold font-mono flex-shrink-0">
              {(user?.name ?? "F").slice(0, 2).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-[12px] font-semibold text-console-text truncate">{user?.name ?? "My Farm"}</div>
              <div className="text-[10px] text-console-mut truncate">{user?.email ?? "farm"}</div>
            </div>
          </div>
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-1.5 px-3">
        {NAV_GROUPS.map((group, gi) => (
          <div key={gi} className={gi ? "mt-3" : "mt-1"}>
            {!collapsed && group.labelKey && (
              <div className="px-2.5 pt-1 pb-1 text-[9.5px] font-bold text-console-mut uppercase tracking-[0.1em]">
                {t(group.labelKey!)}
              </div>
            )}
            {group.items.map((item) => {
              const isActive = item.href === activeHref;
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  data-testid={`nav-${item.href === "/" ? "dashboard" : item.href.slice(1).replace(/\//g, "-")}`}
                  title={collapsed ? t(item.k) : undefined}
                  className={`relative flex items-center gap-2.5 px-2.5 py-2 rounded-[6px] text-sm transition-all ${
                    isActive
                      ? "bg-console3 text-console-text font-semibold"
                      : "text-console-mut hover:bg-console2 hover:text-console-text"
                  } ${collapsed ? "justify-center" : ""}`}
                >
                  {isActive && <span className="absolute left-0 top-[7px] bottom-[7px] w-[3px] rounded-full bg-brand" />}
                  <Icon size={16} className="flex-shrink-0" />
                  {!collapsed && <span className="text-[13px]">{t(item.k)}</span>}
                  {!collapsed && item.badge === "alerts" && (alertCount + unreadCount) > 0 && (
                    <span className="ml-auto text-[10px] font-bold font-mono bg-danger text-white rounded-full px-1.5 min-w-[18px] text-center leading-[18px]">
                      {alertCount + unreadCount}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Ask AI button */}
      <div className="px-3 pb-2.5">
        <button
          onClick={onAskAI}
          className={`w-full flex items-center gap-2 rounded-[9px] py-2.5 text-sm font-semibold text-console-text bg-console2 border border-console-line hover:bg-console3 transition ${
            collapsed ? "justify-center px-2" : "px-3"
          }`}
        >
          <MessageSquareText size={14} className="text-brand" />
          {!collapsed && <span>Ask AI</span>}
        </button>
      </div>

      {/* Bottom: settings + user */}
      <div className="border-t border-console-line py-2 px-3">
        {BOTTOM_ITEMS.map((item) => {
          const isActive = item.href === activeHref;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              data-testid={`nav-${item.href.slice(1).replace(/\//g, "-")}`}
              title={collapsed ? t(item.k) : undefined}
              className={`relative flex items-center gap-2.5 px-2.5 py-2 rounded-[6px] text-sm transition-all ${
                isActive ? "bg-console3 text-console-text font-semibold" : "text-console-mut hover:bg-console2 hover:text-console-text"
              } ${collapsed ? "justify-center" : ""}`}
            >
              {isActive && <span className="absolute left-0 top-[7px] bottom-[7px] w-[3px] rounded-full bg-brand" />}
              <Icon size={16} className="flex-shrink-0" />
              {!collapsed && <span className="text-[13px]">{t(item.k)}</span>}
            </Link>
          );
        })}

        {user && !collapsed && (
          <div className="flex items-center gap-2.5 px-2.5 py-2 mt-1">
            <div className="w-7 h-7 rounded-full bg-console3 flex items-center justify-center text-console-text text-[10px] font-bold flex-shrink-0">
              {user.name.slice(0, 2).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-[12px] font-semibold text-console-text truncate">{user.name}</div>
              <div className="text-[10px] text-console-mut truncate">{user.email}</div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}

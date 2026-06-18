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
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth.store";
import { alertsApi } from "@/lib/api/endpoints/alerts";
import { notificationsApi } from "@/lib/api/endpoints/notifications";
import { queryKeys } from "@/lib/api/queryKeys";
import type { Locale } from "@/i18n/config";

type L = Record<Locale, string>;

interface NavItem {
  href: string;
  icon: React.ElementType;
  label: L;
  badge?: "alerts"; // 통합 알림 배지(관리대상+미읽음 합산)
}

// 메뉴 재설계 2026-06 (docs/menu-redesign-2026-06.md): PigPlan식 그룹 재편 + 알림 통합 + 분만사 제거
const NAV_GROUPS: { label?: L; items: NavItem[] }[] = [
  {
    items: [
      { href: "/", icon: LayoutDashboard, label: { en: "Dashboard", ko: "대시보드", zh: "总览", es: "Panel", vi: "Tổng quan" } },
    ],
  },
  {
    items: [
      { href: "/record", icon: ClipboardList, label: { en: "Record Entry", ko: "기록 입력", zh: "记录录入", es: "Registro", vi: "Nhập dữ liệu" } },
    ],
  },
  {
    label: { en: "Herd", ko: "돈군", zh: "猪群", es: "Hato", vi: "Đàn heo" },
    items: [
      { href: "/sows",      icon: PiggyBank, label: { en: "Sows",      ko: "모돈",   zh: "母猪",   es: "Cerdas",   vi: "Heo nái" } },
      { href: "/boars",     icon: Heart,     label: { en: "Boars",     ko: "웅돈",   zh: "公猪",   es: "Verracos", vi: "Heo nọc" } },
      { href: "/piglets",   icon: Layers,    label: { en: "Piglets",   ko: "자돈",   zh: "仔猪",   es: "Lechones", vi: "Heo con" } },
      { href: "/finishers", icon: Beef,      label: { en: "Finishers", ko: "비육돈", zh: "育肥猪", es: "Engorde",  vi: "Heo thịt" } },
    ],
  },
  {
    label: { en: "Tasks & Alerts", ko: "할 일·알림", zh: "任务与预警", es: "Tareas y alertas", vi: "Việc & cảnh báo" },
    items: [
      { href: "/tasks",  icon: ListTodo,       label: { en: "Today's Tasks", ko: "오늘 할 일", zh: "今日任务", es: "Tareas de hoy", vi: "Việc hôm nay" } },
      { href: "/alerts", icon: AlertTriangle, badge: "alerts", label: { en: "Alerts", ko: "알림", zh: "预警", es: "Alertas", vi: "Cảnh báo" } },
    ],
  },
  {
    label: { en: "Reports", ko: "보고서", zh: "报告", es: "Informes", vi: "Báo cáo" },
    items: [
      { href: "/kpi",                  icon: BarChart3, label: { en: "KPI Summary",       ko: "KPI 현황",    zh: "指标概览", es: "Resumen KPI",       vi: "Tổng quan KPI" } },
      { href: "/reports/daily",        icon: FileText,  label: { en: "Daily Report",      ko: "일일 현황",   zh: "每日现状", es: "Informe diario",    vi: "Báo cáo ngày" } },
      { href: "/reports/reproduction", icon: FileText,  label: { en: "Production (Repro)", ko: "생산성적",    zh: "繁殖成绩", es: "Producción",        vi: "Năng suất sinh sản" } },
      { href: "/reports/grow-finish",  icon: Beef,      label: { en: "Grow-Finish",       ko: "비육성적",    zh: "育肥成绩", es: "Engorde",           vi: "Năng suất vỗ béo" } },
      { href: "/reports",              icon: FileText,  label: { en: "Sow Report",        ko: "모돈 보고서", zh: "母猪报告", es: "Informe de cerdas", vi: "Báo cáo nái" } },
      { href: "/reports/ledger",       icon: ClipboardList, label: { en: "Work Ledger",   ko: "작업대장",    zh: "工作台账", es: "Registro",          vi: "Sổ công việc" } },
      { href: "/reports/prrs",         icon: Dna,       label: { en: "PRRS Genetics",     ko: "PRRS 유전",   zh: "PRRS基因", es: "PRRS genética",     vi: "PRRS di truyền" } },
    ],
  },
  {
    label: { en: "Addons", ko: "Addon", zh: "插件", es: "Addons", vi: "Tiện ích" },
    items: [
      { href: "/addons", icon: Store, label: { en: "Addon Store", ko: "Addon 스토어", zh: "插件商店", es: "Tienda", vi: "Cửa hàng" } },
    ],
  },
];

const BOTTOM_ITEMS: NavItem[] = [
  { href: "/settings", icon: Settings, label: { en: "Settings", ko: "설정", zh: "设置", es: "Configuración", vi: "Cài đặt" } },
];

interface SidebarProps {
  lang?: Locale;
  collapsed?: boolean;
  onCollapse?: () => void;
  onAskAI?: () => void;
}

export function Sidebar({ lang = "ko", collapsed = false, onCollapse, onAskAI }: SidebarProps) {
  const pathname = usePathname();
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

  const t = (obj: L) => obj[lang];

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
      className="hidden md:flex fixed top-0 left-0 h-screen bg-surface border-r border-border flex-col z-50 transition-all duration-200 overflow-hidden"
    >
      {/* Logo */}
      <div className="flex items-center justify-between px-3 py-3 border-b border-border flex-shrink-0">
        {collapsed ? (
          <div className="flex items-center justify-center w-full">
            <Image
              src="/logos/pigos-symbol-light.svg"
              alt="PigOS"
              width={28}
              height={28}
              className="object-contain"
              priority
            />
          </div>
        ) : (
          <Link href="/" className="flex-1">
            <Image
              src="/logos/pigos-logo-horizontal-light.svg"
              alt="PigOS"
              width={96}
              height={36}
              className="object-contain object-left"
              priority
            />
          </Link>
        )}
        <button
          onClick={onCollapse}
          className="ml-1 p-1 rounded-md text-muted hover:text-text hover:bg-bg2 transition flex-shrink-0"
          title={collapsed ? "Expand" : "Collapse"}
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>

      {/* Farm name */}
      {!collapsed && (
        <div className="px-4 py-2.5 border-b border-border">
          <div className="text-[10px] text-muted uppercase tracking-widest mb-0.5">Farm</div>
          <div className="text-xs font-semibold text-text truncate">{user?.name ?? "My Farm"}</div>
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-2">
        {NAV_GROUPS.map((group, gi) => (
          <div key={gi} className="mb-1">
            {!collapsed && group.label && (
              <div className="px-4 pt-3 pb-1 text-[9px] font-bold text-faint uppercase tracking-widest">
                {t(group.label)}
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
                  title={collapsed ? t(item.label) : undefined}
                  className={`flex items-center gap-2.5 mx-2 px-2.5 py-2 rounded-lg text-sm transition-all ${
                    isActive
                      ? "bg-primary/8 text-primary font-semibold"
                      : "text-muted hover:bg-bg2 hover:text-text"
                  } ${collapsed ? "justify-center" : ""}`}
                >
                  <Icon size={15} className="flex-shrink-0" />
                  {!collapsed && <span className="text-[13px]">{t(item.label)}</span>}
                  {!collapsed && item.badge === "alerts" && (alertCount + unreadCount) > 0 && (
                    <span className="ml-auto text-[10px] font-bold bg-danger text-white rounded-full px-1.5 min-w-[18px] text-center leading-[18px]">
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
      <div className="px-3 pb-3">
        <button
          onClick={onAskAI}
          className={`w-full flex items-center gap-2 rounded-xl py-2.5 text-sm font-semibold text-navy bg-primary-soft border border-primary/20 hover:bg-primary/10 hover:border-primary/40 transition ${
            collapsed ? "justify-center px-2" : "px-3"
          }`}
        >
          <MessageSquareText size={14} className="text-primary" />
          {!collapsed && <span>Ask AI</span>}
        </button>
      </div>

      {/* Bottom items */}
      <div className="border-t border-border py-2">
        {BOTTOM_ITEMS.map((item) => {
          const isActive = item.href === activeHref;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              data-testid={`nav-${item.href.slice(1).replace(/\//g, "-")}`}
              title={collapsed ? t(item.label) : undefined}
              className={`flex items-center gap-2.5 mx-2 px-2.5 py-2 rounded-lg text-sm transition-all ${
                isActive ? "bg-primary/8 text-primary font-semibold" : "text-muted hover:bg-bg2 hover:text-text"
              } ${collapsed ? "justify-center" : ""}`}
            >
              <Icon size={15} className="flex-shrink-0" />
              {!collapsed && <span className="text-[13px]">{t(item.label)}</span>}
            </Link>
          );
        })}

        {/* User */}
        {user && !collapsed && (
          <div className="flex items-center gap-2.5 mx-2 px-2.5 py-2 mt-1">
            <div className="w-7 h-7 rounded-full bg-purple flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0">
              {user.name.slice(0, 2).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-[12px] font-semibold text-text truncate">{user.name}</div>
              <div className="text-[10px] text-muted truncate">{user.email}</div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}

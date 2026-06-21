"use client";

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
      { href: "/reports/sow-status",   icon: PiggyBank, label: { en: "Sow Status",        ko: "모돈 현황",   zh: "母猪状态", es: "Estado cerdas",     vi: "Trạng thái nái" } },
      { href: "/reports/daily",        icon: FileText,  label: { en: "Daily Report",      ko: "일일 현황",   zh: "每日现状", es: "Informe diario",    vi: "Báo cáo ngày" } },
      { href: "/reports/farrowing",    icon: Baby,      label: { en: "Farrow & Wean",     ko: "분만·이유",   zh: "分娩断奶", es: "Parto y destete",   vi: "Đẻ & cai sữa" } },
      { href: "/reports/mortality",    icon: TrendingDown, label: { en: "Mortality",      ko: "도폐사·폐사", zh: "淘汰死亡", es: "Mortalidad",        vi: "Loại thải & chết" } },
      { href: "/reports/reproduction", icon: FileText,  label: { en: "Production (Repro)", ko: "생산성적",    zh: "繁殖成绩", es: "Producción",        vi: "Năng suất sinh sản" } },
      { href: "/reports/grow-finish",  icon: Beef,      label: { en: "Grow-Finish",       ko: "비육성적",    zh: "育肥成绩", es: "Engorde",           vi: "Năng suất vỗ béo" } },
      { href: "/reports",              icon: FileText,  label: { en: "Sow Report",        ko: "모돈 보고서", zh: "母猪报告", es: "Informe de cerdas", vi: "Báo cáo nái" } },
      { href: "/reports/ledger",       icon: ClipboardList, label: { en: "Work Ledger",   ko: "작업대장",    zh: "工作台账", es: "Registro",          vi: "Sổ công việc" } },
      { href: "/reports/prrs",         icon: Dna,       label: { en: "PRRS Genetics",     ko: "PRRS 유전",   zh: "PRRS基因", es: "PRRS genética",     vi: "PRRS di truyền" } },
      { href: "/reports/data-quality", icon: ShieldCheck, label: { en: "Data Quality",    ko: "데이터 품질", zh: "数据质量", es: "Calidad de datos",  vi: "Chất lượng dữ liệu" } },
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
      className="hidden md:flex fixed top-0 left-0 h-screen bg-console border-r border-console-line flex-col z-50 transition-all duration-200 overflow-hidden"
    >
      {/* Logo — green mark + PigOS (Operational Console) */}
      <div className="flex items-center gap-2.5 px-4 py-4 border-b border-console-line flex-shrink-0">
        <Link href="/" className="flex items-center gap-2.5 flex-1 min-w-0">
          <span className="w-[30px] h-[30px] rounded-lg bg-brand flex items-center justify-center flex-shrink-0">
            <PiggyBank size={18} className="text-white" />
          </span>
          {!collapsed && <span className="text-[16px] font-bold text-console-text tracking-tight">PigOS</span>}
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
            {!collapsed && group.label && (
              <div className="px-2.5 pt-1 pb-1 text-[9.5px] font-bold text-console-mut uppercase tracking-[0.1em]">
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
                  className={`relative flex items-center gap-2.5 px-2.5 py-2 rounded-[6px] text-sm transition-all ${
                    isActive
                      ? "bg-console3 text-console-text font-semibold"
                      : "text-console-mut hover:bg-console2 hover:text-console-text"
                  } ${collapsed ? "justify-center" : ""}`}
                >
                  {isActive && <span className="absolute left-0 top-[7px] bottom-[7px] w-[3px] rounded-full bg-brand" />}
                  <Icon size={16} className="flex-shrink-0" />
                  {!collapsed && <span className="text-[13px]">{t(item.label)}</span>}
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
              title={collapsed ? t(item.label) : undefined}
              className={`relative flex items-center gap-2.5 px-2.5 py-2 rounded-[6px] text-sm transition-all ${
                isActive ? "bg-console3 text-console-text font-semibold" : "text-console-mut hover:bg-console2 hover:text-console-text"
              } ${collapsed ? "justify-center" : ""}`}
            >
              {isActive && <span className="absolute left-0 top-[7px] bottom-[7px] w-[3px] rounded-full bg-brand" />}
              <Icon size={16} className="flex-shrink-0" />
              {!collapsed && <span className="text-[13px]">{t(item.label)}</span>}
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

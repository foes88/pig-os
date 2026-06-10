"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  PiggyBank,
  Baby,
  Heart,
  ClipboardList,
  BarChart3,
  FileText,
  MessageSquareText,
  Layers,
  Store,
  Bell,
  Settings,
  ChevronLeft,
  ChevronRight,
  Beef,
} from "lucide-react";
import { useAuthStore } from "@/store/auth.store";
import type { Locale } from "@/i18n/config";

type L = Record<Locale, string>;

interface NavItem {
  href: string;
  icon: React.ElementType;
  label: L;
}

const NAV_GROUPS: { label?: L; items: NavItem[] }[] = [
  {
    items: [
      {
        href: "/",
        icon: LayoutDashboard,
        label: { en: "Dashboard", ko: "대시보드", zh: "总览", es: "Panel", vi: "Tổng quan" },
      },
    ],
  },
  {
    label: { en: "Herd", ko: "돈군 관리", zh: "猪群管理", es: "Hato", vi: "Đàn heo" },
    items: [
      { href: "/sows",      icon: PiggyBank, label: { en: "Sows",      ko: "모돈",   zh: "母猪",   es: "Cerdas",   vi: "Heo nái" } },
      { href: "/boars",     icon: Heart,     label: { en: "Boars",     ko: "웅돈",   zh: "公猪",   es: "Verracos", vi: "Heo nọc" } },
      { href: "/piglets",   icon: Layers,    label: { en: "Piglets",   ko: "자돈",   zh: "仔猪",   es: "Lechones", vi: "Heo con" } },
      { href: "/finishers", icon: Beef,      label: { en: "Finishers", ko: "비육돈", zh: "育肥猪", es: "Engorde",  vi: "Heo thịt" } },
    ],
  },
  {
    label: { en: "Records", ko: "기록", zh: "记录", es: "Registros", vi: "Ghi chép" },
    items: [
      { href: "/record",    icon: ClipboardList, label: { en: "Data Entry", ko: "기록 입력", zh: "数据录入", es: "Captura de datos", vi: "Nhập dữ liệu" } },
      { href: "/farrowing", icon: Baby,          label: { en: "Farrowing",  ko: "분만사",    zh: "产房",     es: "Maternidad",       vi: "Chuồng đẻ" } },
    ],
  },
  {
    label: { en: "Analytics", ko: "분석", zh: "分析", es: "Análisis", vi: "Phân tích" },
    items: [
      { href: "/kpi",     icon: BarChart3,   label: { en: "KPI",     ko: "KPI",    zh: "指标",  es: "KPI",      vi: "KPI" } },
      { href: "/reports", icon: FileText,    label: { en: "Reports", ko: "보고서", zh: "报告",  es: "Informes", vi: "Báo cáo" } },
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
  { href: "/notifications", icon: Bell,     label: { en: "Notifications", ko: "알림", zh: "通知", es: "Notificaciones", vi: "Thông báo" } },
  { href: "/settings",      icon: Settings, label: { en: "Settings",      ko: "설정", zh: "设置", es: "Configuración",   vi: "Cài đặt" } },
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

  const t = (obj: L) => obj[lang];

  return (
    <aside
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
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname === item.href || pathname?.startsWith(item.href + "/");
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  title={collapsed ? t(item.label) : undefined}
                  className={`flex items-center gap-2.5 mx-2 px-2.5 py-2 rounded-lg text-sm transition-all ${
                    isActive
                      ? "bg-primary/8 text-primary font-semibold"
                      : "text-muted hover:bg-bg2 hover:text-text"
                  } ${collapsed ? "justify-center" : ""}`}
                >
                  <Icon size={15} className="flex-shrink-0" />
                  {!collapsed && <span className="text-[13px]">{t(item.label)}</span>}
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
          className={`w-full flex items-center gap-2 rounded-xl py-2.5 text-sm font-semibold text-white transition ${
            collapsed ? "justify-center px-2" : "px-3"
          }`}
          style={{ background: "linear-gradient(135deg, #2563EB 0%, #7C3AED 100%)" }}
        >
          <MessageSquareText size={14} />
          {!collapsed && <span>Ask AI</span>}
        </button>
      </div>

      {/* Bottom items */}
      <div className="border-t border-border py-2">
        {BOTTOM_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
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

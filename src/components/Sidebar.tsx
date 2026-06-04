"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/store/auth.store";

interface NavItem {
  href: string;
  icon: string;
  label: { en: string; ko: string };
  badge?: string | number | null;
}

const NAV_GROUPS: { label?: { en: string; ko: string }; items: NavItem[] }[] = [
  {
    items: [
      { href: "/", icon: "⊞", label: { en: "Home", ko: "홈" } },
      { href: "/sows",      icon: "⬡", label: { en: "Sows", ko: "모돈" }, badge: null },
      { href: "/farrowing", icon: "◫", label: { en: "Farrowing", ko: "분만사" } },
      { href: "/reports",   icon: "▤", label: { en: "Reports", ko: "보고서" } },
    ],
  },
  {
    label: { en: "Production", ko: "생산돈" },
    items: [
      { href: "/piglets",   icon: "◎", label: { en: "Piglets", ko: "자돈" } },
      { href: "/finishers", icon: "▣", label: { en: "Finishers", ko: "비육돈" } },
    ],
  },
  {
    label: { en: "Addons", ko: "Addon" },
    items: [
      { href: "/addons",    icon: "✦", label: { en: "Addon Store", ko: "Addon 스토어" } },
    ],
  },
];

const BOTTOM_ITEMS = [
  { href: "/notifications", icon: "🔔", label: { en: "Notifications", ko: "알림" } },
  { href: "/settings",      icon: "⚙", label: { en: "Settings", ko: "설정" } },
];

interface SidebarProps {
  lang?: "en" | "ko";
  collapsed?: boolean;
  onCollapse?: () => void;
  onAskAI?: () => void;
}

export function Sidebar({ lang = "ko", collapsed = false, onCollapse, onAskAI }: SidebarProps) {
  const pathname = usePathname();
  const user = useAuthStore((s) => s.user);
  const w = collapsed ? 64 : 224;

  const t = (obj: { en: string; ko: string }) => obj[lang];

  return (
    <aside
      style={{ width: w }}
      className="hidden md:flex fixed top-0 left-0 h-screen bg-surface border-r border-border flex-col z-50 transition-all duration-200 overflow-hidden"
    >
      {/* Logo + collapse toggle */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-border flex-shrink-0">
        {!collapsed && (
          <div className="flex items-center gap-2">
            {/* Logo mark */}
            <div className="w-7 h-7 rounded-lg bg-navy flex items-center justify-center flex-shrink-0">
              <span className="text-white text-xs font-black">P</span>
              <span className="absolute w-2 h-1.5 bg-snout rounded-sm" style={{ marginTop: 4, marginLeft: 4 }} />
            </div>
            <span className="text-sm font-black tracking-tight text-text">
              Pig<span className="text-primary">OS</span>
            </span>
          </div>
        )}
        {collapsed && (
          <div className="w-7 h-7 rounded-lg bg-navy flex items-center justify-center mx-auto">
            <span className="text-white text-xs font-black">P</span>
          </div>
        )}
        <button
          onClick={onCollapse}
          className={`text-muted hover:text-text transition text-xs ${collapsed ? "mx-auto mt-2" : ""}`}
          title={collapsed ? "Expand" : "Collapse"}
        >
          {collapsed ? "›" : "‹"}
        </button>
      </div>

      {/* Farm name */}
      {!collapsed && (
        <div className="px-4 py-2.5 border-b border-border">
          <div className="text-[10px] text-muted uppercase tracking-widest mb-0.5">Farm</div>
          <div className="text-xs font-semibold text-text truncate">
            {user?.name ?? "My Farm"}
          </div>
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-2">
        {NAV_GROUPS.map((group, gi) => (
          <div key={gi} className="mb-1">
            {!collapsed && group.label && (
              <div className="px-4 py-1 text-[9px] font-bold text-faint uppercase tracking-widest">
                {t(group.label)}
              </div>
            )}
            {group.items.map((item) => {
              const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  title={collapsed ? t(item.label) : undefined}
                  className={`flex items-center gap-3 mx-2 px-2.5 py-2 rounded-lg text-sm transition-all ${
                    isActive
                      ? "bg-primary-soft text-primary font-semibold"
                      : "text-muted hover:bg-bg2 hover:text-text"
                  } ${collapsed ? "justify-center" : ""}`}
                >
                  <span className="text-base flex-shrink-0">{item.icon}</span>
                  {!collapsed && (
                    <span className="flex-1 text-[13px]">{t(item.label)}</span>
                  )}
                  {!collapsed && item.badge && (
                    <span className="font-mono text-[10px] text-muted">{item.badge}</span>
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
          className={`w-full flex items-center gap-2.5 rounded-xl py-2.5 text-sm font-semibold text-white transition ${
            collapsed ? "justify-center px-2" : "px-3"
          }`}
          style={{ background: "linear-gradient(135deg, #2563EB 0%, #7C3AED 100%)" }}
        >
          <span className="text-base">✦</span>
          {!collapsed && <span>PigOS AI</span>}
        </button>
      </div>

      {/* Bottom items */}
      <div className="border-t border-border py-2">
        {BOTTOM_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? t(item.label) : undefined}
              className={`flex items-center gap-3 mx-2 px-2.5 py-2 rounded-lg text-sm transition-all ${
                isActive ? "bg-primary-soft text-primary font-semibold" : "text-muted hover:bg-bg2 hover:text-text"
              } ${collapsed ? "justify-center" : ""}`}
            >
              <span className="text-base flex-shrink-0">{item.icon}</span>
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

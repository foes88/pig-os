"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Locale } from "@/i18n/config";

interface BottomNavProps {
  lang?: Locale;
  onAskAI?: () => void;
  alertCount?: number;
}

type L = Record<Locale, string>;

const TABS: { href: string | null; icon: string; label: L; isAI?: boolean; badge?: number }[] = [
  { href: "/",              icon: "⊞", label: { en: "Home",   ko: "홈",    zh: "首页", es: "Inicio",    vi: "Trang chủ" } },
  { href: "/sows",          icon: "⬡", label: { en: "Sows",   ko: "모돈",  zh: "母猪", es: "Cerdas",    vi: "Nái" } },
  { href: null,             icon: "✦", label: { en: "AI",     ko: "AI",    zh: "AI",   es: "IA",        vi: "AI" }, isAI: true },
  { href: "/notifications", icon: "🔔", label: { en: "Alerts", ko: "알림",  zh: "通知", es: "Alertas",   vi: "Cảnh báo" }, badge: 3 },
  { href: "/settings",      icon: "⚙",  label: { en: "More",  ko: "더보기", zh: "更多", es: "Más",       vi: "Thêm" } },
];

export function BottomNav({ lang = "ko", onAskAI, alertCount = 0 }: BottomNavProps) {
  const pathname = usePathname();

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-surface border-t border-border grid grid-cols-5 pb-safe">
      {TABS.map((tab, i) => {
        if (tab.isAI) {
          return (
            <button
              key={i}
              onClick={onAskAI}
              className="flex flex-col items-center justify-center py-2 gap-1"
            >
              <div
                className="w-10 h-10 rounded-xl -mt-2 flex items-center justify-center text-white text-lg"
                style={{
                  background: "linear-gradient(135deg, #2563EB 0%, #7C3AED 100%)",
                  boxShadow: "0 4px 12px rgba(37,99,235,.4)",
                }}
              >
                {tab.icon}
              </div>
              <span className="text-[10px] font-semibold text-primary">{tab.label[lang]}</span>
            </button>
          );
        }

        const isActive = tab.href && (pathname === tab.href || pathname?.startsWith(tab.href + "/"));
        const actualBadge = tab.href === "/notifications" ? alertCount : (tab.badge ?? 0);

        return (
          <Link
            key={i}
            href={tab.href ?? "#"}
            className="flex flex-col items-center justify-center py-3 gap-1 relative"
          >
            <span className={`text-xl ${isActive ? "text-primary" : "text-faint"}`}>
              {tab.icon}
            </span>
            {actualBadge > 0 && (
              <span className="absolute top-2 right-1/4 min-w-[14px] h-3.5 px-1 rounded-full bg-red text-white font-mono text-[9px] font-bold flex items-center justify-center">
                {actualBadge}
              </span>
            )}
            <span className={`text-[10px] font-medium ${isActive ? "text-primary font-semibold" : "text-faint"}`}>
              {tab.label[lang]}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}

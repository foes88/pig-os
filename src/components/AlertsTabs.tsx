"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLocale } from "next-intl";

// 메뉴 통합(2026-06): 사이드바엔 '알림' 1개(/alerts)만 두고, 관리대상↔시스템알림은 탭으로 전환.
// 자체 라벨(5개어)로 messages 의존 없이 동작.
const TABS = [
  { href: "/alerts",        label: { en: "Overdue & Cull", ko: "관리 대상",  zh: "管理对象", es: "Atrasados",      vi: "Cần xử lý" } },
  { href: "/notifications", label: { en: "Notifications",  ko: "시스템 알림", zh: "系统通知", es: "Notificaciones", vi: "Thông báo" } },
] as const;

type Loc = "en" | "ko" | "zh" | "es" | "vi";

export function AlertsTabs() {
  const pathname = usePathname();
  const locale = useLocale() as Loc;
  return (
    <div className="flex gap-1 mb-5 border-b border-border">
      {TABS.map((tab) => {
        const active = pathname === tab.href;
        return (
          <Link
            key={tab.href}
            href={tab.href}
            data-testid={`alerts-tab-${tab.href.slice(1)}`}
            className={`px-4 py-2 text-sm font-semibold -mb-px border-b-2 transition ${
              active
                ? "border-primary text-primary"
                : "border-transparent text-muted hover:text-text"
            }`}
          >
            {tab.label[locale] ?? tab.label.en}
          </Link>
        );
      })}
    </div>
  );
}

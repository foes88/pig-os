"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLocale } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { alertsApi } from "@/lib/api/endpoints/alerts";
import { notificationsApi } from "@/lib/api/endpoints/notifications";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";

// 메뉴 통합(2026-06): 사이드바엔 '알림' 1개(/alerts)만 두고, 관리대상↔시스템알림은 탭으로 전환.
// 각 탭에 건수 배지 표기 — 사이드바 합산 배지(관리대상+미읽음)와 실제 위치를 일치시켜
// "배지는 뜨는데 착지 탭이 비어 보임" 혼란 제거(BUG-001).
const TABS = [
  { href: "/alerts",        key: "overdue" as const, label: { en: "Overdue & Cull", ko: "관리 대상",  zh: "管理对象", es: "Atrasados",      vi: "Cần xử lý", th: "ค้างดำเนินการ", pt: "Atrasados", ru: "Просроченные" } },
  { href: "/notifications", key: "unread"  as const, label: { en: "Notifications",  ko: "시스템 알림", zh: "系统通知", es: "Notificaciones", vi: "Thông báo",  th: "การแจ้งเตือน", pt: "Notificações", ru: "Оповещения" } },
] as const;

type Loc = "en" | "ko" | "zh" | "es" | "vi" | "th" | "pt" | "ru";

export function AlertsTabs() {
  const pathname = usePathname();
  const locale = useLocale() as Loc;
  const farmId = useAuthStore((s) => s.activeFarmId);

  const { data: overdue } = useQuery({
    queryKey: queryKeys.alerts.overdue(farmId ?? ""),
    queryFn: () => alertsApi.overdue(farmId!),
    enabled: !!farmId,
  });
  const { data: notif } = useQuery({
    queryKey: queryKeys.notifications.unread(farmId ?? ""),
    queryFn: () => notificationsApi.list({ farmId: farmId!, limit: 0 }),
    enabled: !!farmId,
  });

  const counts: Record<"overdue" | "unread", number> = {
    overdue: overdue?.total ?? 0,
    unread: notif?.unread_count ?? 0,
  };

  return (
    <div className="flex gap-1 mb-5 border-b border-border">
      {TABS.map((tab) => {
        const active = pathname === tab.href;
        const n = counts[tab.key];
        return (
          <Link
            key={tab.href}
            href={tab.href}
            data-testid={`alerts-tab-${tab.href.slice(1)}`}
            className={`px-4 py-2 text-sm font-semibold -mb-px border-b-2 transition flex items-center gap-1.5 ${
              active
                ? "border-primary text-primary"
                : "border-transparent text-muted hover:text-text"
            }`}
          >
            {tab.label[locale] ?? tab.label.en}
            {n > 0 && (
              <span className={`inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full text-[11px] font-bold ${
                active ? "bg-primary text-white" : "bg-danger text-white"
              }`}>
                {n}
              </span>
            )}
          </Link>
        );
      })}
    </div>
  );
}

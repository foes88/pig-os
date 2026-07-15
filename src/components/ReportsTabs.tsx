"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";

// 생산성적 보고서 단일화면 통합 — 흩어진 리포트를 하나의 탭 허브로.
// 라벨은 messages/*.json 의 reportsTabs 네임스페이스(파일 단일소스, 인라인 제거).
const TABS = [
  { href: "/reports",                    k: "production" },
  { href: "/reports/reproduction",       k: "reproduction" },
  { href: "/reports/trend",              k: "trend" },
  { href: "/reports/monthly",            k: "monthly" },
  { href: "/reports/farrowing",          k: "farrowing" },
  { href: "/reports/grow-finish",        k: "growFinish" },
  { href: "/reports/cost",               k: "cost" },
  { href: "/reports/comprehensive-daily", k: "daily" },
] as const;

export function ReportsTabs() {
  const pathname = usePathname();
  const t = useTranslations("reportsTabs");
  return (
    <div className="flex gap-1 mb-5 border-b border-border overflow-x-auto">
      {TABS.map((tab) => {
        const active = pathname === tab.href;
        return (
          <Link
            key={tab.href}
            href={tab.href}
            data-testid={`reports-tab-${tab.href.slice(1).replace(/\//g, "-") || "production"}`}
            className={`px-4 py-2 text-sm font-semibold -mb-px border-b-2 whitespace-nowrap transition ${
              active ? "border-primary text-primary" : "border-transparent text-muted hover:text-text"
            }`}
          >
            {t(tab.k)}
          </Link>
        );
      })}
    </div>
  );
}

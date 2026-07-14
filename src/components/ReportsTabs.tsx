"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLocale } from "next-intl";

// 생산성적 보고서 단일화면 통합 — 흩어진 리포트를 하나의 탭 허브로.
// 자체 라벨(8개어)로 messages 의존 없이 동작.
const TABS = [
  { href: "/reports",                    label: { en: "Production", ko: "생산성적", zh: "生产成绩", es: "Producción", vi: "Năng suất", th: "ผลผลิต", pt: "Produção", ru: "Продуктивность" } },
  { href: "/reports/reproduction",       label: { en: "Reproduction", ko: "번식성적", zh: "繁殖成绩", es: "Reproducción", vi: "Sinh sản", th: "การสืบพันธุ์", pt: "Reprodução", ru: "Воспроизводство" } },
  { href: "/reports/trend",              label: { en: "Trend", ko: "연도추세", zh: "年度趋势", es: "Tendencia", vi: "Xu hướng", th: "แนวโน้มรายปี", pt: "Tendência", ru: "Динамика" } },
  { href: "/reports/monthly",            label: { en: "Monthly", ko: "월별종합", zh: "月度综合", es: "Mensual", vi: "Hàng tháng", th: "รายเดือน", pt: "Mensal", ru: "Помесячно" } },
  { href: "/reports/farrowing",          label: { en: "Farrowing", ko: "분만성적", zh: "分娩成绩", es: "Partos", vi: "Đẻ", th: "การคลอด", pt: "Partos", ru: "Опоросы" } },
  { href: "/reports/grow-finish",        label: { en: "Grow-Finish", ko: "비육성적", zh: "育肥成绩", es: "Engorde", vi: "Vỗ béo", th: "ขุน", pt: "Engorda", ru: "Откорм" } },
  { href: "/reports/cost",               label: { en: "Cost / Revenue", ko: "원가·수익", zh: "成本·收益", es: "Costo·Ingreso", vi: "Chi phí·Doanh thu", th: "ต้นทุน·รายได้", pt: "Custo·Receita", ru: "Затраты·Доход" } },
  { href: "/reports/comprehensive-daily", label: { en: "Daily (Full)", ko: "종합일보", zh: "综合日报", es: "Diario", vi: "Báo cáo ngày", th: "รายวัน (เต็ม)", pt: "Diário", ru: "Сводка за день" } },
] as const;

type Loc = "en" | "ko" | "zh" | "es" | "vi" | "th" | "pt" | "ru";

export function ReportsTabs() {
  const pathname = usePathname();
  const locale = useLocale() as Loc;
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
            {tab.label[locale] ?? tab.label.en}
          </Link>
        );
      })}
    </div>
  );
}

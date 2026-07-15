"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { CalendarRange, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { ReportsTabs } from "@/components/ReportsTabs";
import { ReportExportBar } from "@/components/ReportExportBar";
import { MiniLineChart } from "@/components/MiniLineChart";
import { downloadCsv } from "@/lib/utils/csv";
import { localToday } from "@/lib/date";
import { reportsApi } from "@/lib/api/endpoints/reports";
import { kpiApi } from "@/lib/api/endpoints/kpi";
import { useAuthStore } from "@/store/auth.store";
import type { KpiTrend, ReproductionRow } from "@/types/api.types";

// 자족적 다국어(신규 리포트 — 인라인, cost/trend와 동일 패턴).
const PRESETS = [
  { key: "m6", months: 6 },
  { key: "m12", months: 12 },
  { key: "m24", months: 24 },
];

function monthsAgoISO(n: number): string {
  const d = new Date();
  d.setDate(1); // 월말일(31일 등)에서 setMonth 오버플로로 시작월이 밀리는 버그 방지
  d.setMonth(d.getMonth() - n);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-01`;
}

// 최근 월 vs 직전 월 방향 표시 (higherBetter=true → 상승이 좋음)
function Delta({ cur, prev, higherBetter }: { cur: number | null; prev: number | null; higherBetter: boolean }) {
  if (cur == null || prev == null || cur === prev) return <Minus size={14} className="text-text3" />;
  const up = cur > prev;
  const good = up === higherBetter;
  const Icon = up ? TrendingUp : TrendingDown;
  return <Icon size={14} className={good ? "text-success" : "text-danger"} />;
}

export default function MonthlyDashboardPage() {
  const t = useTranslations("reportMonthly");
  const farmId = useAuthStore((s) => s.activeFarmId);
  const [months, setMonths] = useState(12);

  const trendQ = useQuery({
    queryKey: ["reports", "monthly-trend", farmId, months],
    queryFn: () => kpiApi.trend(farmId!, "psy", months),
    enabled: !!farmId,
  });
  const prodQ = useQuery({
    queryKey: ["reports", "monthly-prod", farmId, months],
    queryFn: () => reportsApi.productionSummary(farmId!, monthsAgoISO(months - 1), localToday(), "monthly", "period"),
    enabled: !!farmId,
  });

  if (!farmId) return <div className="p-7 text-text3">{t("selectFarm")}</div>;

  const trend: KpiTrend[] = trendQ.data ?? [];
  const prod: ReproductionRow[] = prodQ.data?.rows ?? [];
  const isLoading = trendQ.isLoading || prodQ.isLoading;
  const hasData = trend.some((t) => t.psy != null || t.npd != null) || prod.length > 0;

  const last = trend[trend.length - 1];
  const prev = trend[trend.length - 2];

  const exportCsv = () => {
    // 추세(KPI) + 물량을 월 키로 병합
    const prodByMonth = new Map(prod.map((r) => [r.period, r]));
    const allMonths = Array.from(new Set([...trend.map((t) => t.period), ...prod.map((r) => r.period)])).sort();
    downloadCsv(
      `pigos_monthly_${farmId}_${allMonths.length}mo.csv`,
      [t("month"), t("psy"), t("npd"), `${t("fr")}(%)`, t("matings"), t("farrowings"), t("weanings"), t("tb"), t("ba"), t("weaned")],
      allMonths.map((m) => {
        const t = trend.find((x) => x.period === m);
        const p = prodByMonth.get(m);
        return [m, t?.psy ?? null, t?.npd ?? null, t?.farrowing_rate ?? null,
          p?.total_matings ?? null, p?.total_farrowings ?? null, p?.total_weanings ?? null,
          p?.avg_tb ?? null, p?.avg_ba ?? null, p?.avg_weaned ?? null];
      }),
    );
  };

  const psyPts = trend.map((t) => ({ x: t.period.slice(2), y: t.psy }));
  const npdPts = trend.map((t) => ({ x: t.period.slice(2), y: t.npd }));
  const frPts = trend.map((t) => ({ x: t.period.slice(2), y: t.farrowing_rate }));

  return (
    <div className="p-7 max-w-5xl print-area">
      <div className="no-print"><ReportsTabs /></div>
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-[22px] font-extrabold tracking-tight flex items-center gap-2">
            <CalendarRange size={20} className="text-primary" />{t("title")}
          </h1>
          <p className="text-xs text-text3 mt-0.5">{t("sub")}</p>
        </div>
        <ReportExportBar onCsv={exportCsv} csvDisabled={!hasData} />
      </div>

      <div className="no-print flex gap-2 mb-5">
        {PRESETS.map((p) => (
          <button
            key={p.months}
            onClick={() => setMonths(p.months)}
            className={`text-xs font-semibold rounded-full px-3.5 py-1.5 border transition ${
              months === p.months ? "bg-primary text-white border-primary" : "border-border text-text3 hover:border-primary"
            }`}
          >
            {t(p.key)}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="h-64 bg-border rounded-2xl animate-pulse" />
      ) : !hasData ? (
        <div className="border border-border rounded-2xl py-16 text-center text-text3">{t("noData")}</div>
      ) : (
        <>
          {/* 최근 월 헤드라인 카드 */}
          {last && (
            <div className="grid grid-cols-3 gap-3 mb-6">
              {([
                { label: t("psy"), cur: last.psy, prev: prev?.psy ?? null, higher: true },
                { label: t("npd"), cur: last.npd, prev: prev?.npd ?? null, higher: false },
                { label: t("fr"), cur: last.farrowing_rate, prev: prev?.farrowing_rate ?? null, higher: true, pct: true },
              ] as const).map((k) => (
                <div key={k.label} className="bg-surface border border-border rounded-2xl p-4">
                  <div className="text-[11px] font-bold uppercase tracking-wide text-text3 mb-1">{k.label}</div>
                  <div className="flex items-baseline gap-1.5">
                    <span className="font-mono text-2xl font-extrabold">{k.cur != null ? k.cur : "—"}{"pct" in k && k.pct && k.cur != null ? "%" : ""}</span>
                    <Delta cur={k.cur} prev={k.prev} higherBetter={k.higher} />
                  </div>
                  <div className="text-[10px] text-text3 mt-0.5">{t("latest")} · {last.period}</div>
                </div>
              ))}
            </div>
          )}

          {/* 월별 추세 3종 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-surface border border-border rounded-2xl p-4">
              <h2 className="text-sm font-bold mb-1">{t("psy")}</h2>
              <MiniLineChart points={psyPts} color="var(--color-primary, #2563eb)" label={t("psy")} />
            </div>
            <div className="bg-surface border border-border rounded-2xl p-4">
              <h2 className="text-sm font-bold mb-1">{t("npd")}</h2>
              <MiniLineChart points={npdPts} color="var(--color-purple, #7c3aed)" label={t("npd")} />
            </div>
            <div className="bg-surface border border-border rounded-2xl p-4">
              <h2 className="text-sm font-bold mb-1">{t("fr")}</h2>
              <MiniLineChart points={frPts} color="var(--color-success, #16a34a)" label={t("fr")} />
            </div>
          </div>

          {/* 월별 물량 표 */}
          <div className="border border-border rounded-2xl overflow-x-auto">
            <div className="px-4 pt-3 pb-1 text-xs font-bold text-text3">{t("volumes")}</div>
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-bg2 text-text3 text-[11px] uppercase tracking-wide">
                  <th className="text-left font-semibold px-3 py-2.5">{t("month")}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{t("matings")}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{t("farrowings")}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{t("weanings")}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{t("tb")}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{t("ba")}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{t("weaned")}</th>
                </tr>
              </thead>
              <tbody>
                {prod.map((r) => (
                  <tr key={r.period} className="border-t border-border">
                    <td className="px-3 py-2.5 font-mono font-semibold">{r.period}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.total_matings}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.total_farrowings}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.total_weanings}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.avg_tb ?? "-"}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.avg_ba ?? "-"}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.avg_weaned ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

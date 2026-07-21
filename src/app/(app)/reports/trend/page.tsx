"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { TrendingUp } from "lucide-react";
import { ReportsTabs } from "@/components/ReportsTabs";
import { ReportExportBar } from "@/components/ReportExportBar";
import { MiniLineChart } from "@/components/MiniLineChart";
import { downloadCsv } from "@/lib/utils/csv";
import { reportsApi } from "@/lib/api/endpoints/reports";
import { useAuthStore } from "@/store/auth.store";
import type { AnnualKpiRow } from "@/types/api.types";

// 자족적 다국어(신규 리포트 — messages 부분갱신 대신 인라인, cost/data-monitor와 동일 패턴).
const PRESETS = [
  { key: "y3", years: 3 },
  { key: "y5", years: 5 },
  { key: "y10", years: 10 },
];

export default function KpiTrendPage() {
  const t = useTranslations("reportTrend");
  const farmId = useAuthStore((s) => s.activeFarmId);
  const [years, setYears] = useState(5);

  const { data, isLoading } = useQuery({
    queryKey: ["reports", "annual-kpi", farmId, years],
    queryFn: () => reportsApi.annualKpi(farmId!, years),
    enabled: !!farmId,
  });

  if (!farmId) return <div className="p-7 text-text3">{t("selectFarm")}</div>;

  const rows: AnnualKpiRow[] = data?.rows ?? [];
  const hasData = rows.some((r) => r.psy != null || r.npd != null);
  // 농장 국가 목표(추세 차트 기준선)
  const ownBench = data?.country_benchmarks?.find((b) => b.country === data?.country_scope)
    ?? data?.country_benchmarks?.[0];

  const exportCsv = () => {
    downloadCsv(
      `pigos_kpi_trend_${farmId}_${years}y.csv`,
      [t("year"), t("psy"), t("npd"), `${t("fr")}(%)`, t("farrowings"), t("matings"), t("avgSows"), t("weaned")],
      rows.map((r) => [r.year, r.psy, r.npd, r.farrowing_rate, r.total_farrowings, r.total_matings, r.avg_sows, r.total_weaned]),
    );
  };

  const psyPts = rows.map((r) => ({ x: String(r.year), y: r.psy }));
  const npdPts = rows.map((r) => ({ x: String(r.year), y: r.npd }));

  return (
    <div className="p-7 max-w-[1600px] print-area">
      <div className="no-print"><ReportsTabs /></div>
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-[22px] font-extrabold tracking-tight flex items-center gap-2">
            <TrendingUp size={20} className="text-primary" />{t("title")}
          </h1>
          <p className="text-xs text-text3 mt-0.5">{t("sub")}</p>
        </div>
        <ReportExportBar onCsv={exportCsv} csvDisabled={!hasData} />
      </div>

      <div className="no-print flex gap-2 mb-5">
        {PRESETS.map((p) => (
          <button
            key={p.years}
            onClick={() => setYears(p.years)}
            className={`text-xs font-semibold rounded-full px-3.5 py-1.5 border transition ${
              years === p.years ? "bg-primary text-white border-primary" : "border-border text-text3 hover:border-primary"
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
          {/* 추세 차트 2종 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="bg-surface border border-border rounded-2xl p-4">
              <div className="flex items-baseline justify-between mb-1">
                <h2 className="text-sm font-bold">{t("psy")}</h2>
                <span className="text-[10px] text-success">{t("higher")}</span>
              </div>
              <MiniLineChart points={psyPts} benchmark={ownBench?.psy} color="var(--color-primary, #2563eb)" label={t("psy")} />
            </div>
            <div className="bg-surface border border-border rounded-2xl p-4">
              <div className="flex items-baseline justify-between mb-1">
                <h2 className="text-sm font-bold">{t("npd")}</h2>
                <span className="text-[10px] text-text3">{t("lower")}</span>
              </div>
              <MiniLineChart points={npdPts} benchmark={ownBench?.npd} color="var(--color-purple, #7c3aed)" label={t("npd")} />
            </div>
          </div>

          {/* 국가 벤치마크 병기 */}
          {(data?.country_benchmarks?.length ?? 0) > 0 && (
            <div className="bg-surface border border-border rounded-2xl overflow-x-auto mb-6">
              <div className="px-4 pt-3 pb-1 text-xs font-bold text-text3">{t("bench")}</div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-bg2 text-text3 text-[11px] uppercase tracking-wide">
                    <th className="text-left font-semibold px-4 py-2">{t("year")}</th>
                    {data!.country_benchmarks.map((b) => (
                      <th key={b.country} className="text-right font-semibold px-4 py-2 font-mono">{b.country}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {([["psy", t("psy")], ["npd", t("npd")], ["farrowing_rate", t("fr")]] as const).map(([k, lbl]) => (
                    <tr key={k} className="border-t border-border">
                      <td className="px-4 py-2 font-semibold">{lbl} {t("target")}</td>
                      {data!.country_benchmarks.map((b) => (
                        <td key={b.country} className="px-4 py-2 text-right font-mono tabular-nums text-text2">
                          {b[k] != null ? (k === "farrowing_rate" ? `${b[k]}%` : b[k]) : "-"}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* 연도별 데이터 표 */}
          <div className="border border-border rounded-2xl overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-bg2 text-text3 text-[11px] uppercase tracking-wide">
                  <th className="text-left font-semibold px-3 py-2.5">{t("year")}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{t("psy")}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{t("npd")}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{t("fr")}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{t("farrowings")}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{t("matings")}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{t("avgSows")}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{t("weaned")}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.year} className="border-t border-border">
                    <td className="px-3 py-2.5 font-mono font-semibold">{r.year}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.psy ?? "-"}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.npd ?? "-"}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.farrowing_rate != null ? `${r.farrowing_rate}%` : "-"}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.total_farrowings}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.total_matings}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.avg_sows ?? "-"}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.total_weaned}</td>
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

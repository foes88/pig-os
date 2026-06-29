"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { kpiApi } from "@/lib/api/endpoints/kpi";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import { ReportsTabs } from "@/components/ReportsTabs";
import { buildReproCsvRows } from "@/lib/reports/csv";
import type { KpiTrend } from "@/types/api.types";

// label/unit은 렌더 시 t()로 해석 (모듈 레벨이라 키만 보관). 색은 Forest 토큰 클래스(raw hex 금지).
const KPI_LIST = [
  { key: "psy",            label: "PSY",  unitKey: "unitPsy",     good: "high", colorClass: "text-success" },
  { key: "npd",            label: "NPD",  unitKey: "unitDays",    good: "low",  colorClass: "text-insufficient" },
  { key: "farrowing_rate", labelKey: "kpiFarrowingRate", unitKey: "unitPercent", good: "high", colorClass: "text-brand-2" },
] as const;

type KpiKey = (typeof KPI_LIST)[number]["key"];

// ─── Simple SVG bar chart ─────────────────────────────────────────────────────

function BarChart({ data, kpiKey, colorClass }: { data: KpiTrend[]; kpiKey: KpiKey; colorClass: string }) {
  const values = data.map((d) => d[kpiKey] ?? 0);
  const max = Math.max(...values, 0.001);

  const W = 560;
  const H = 160;
  const PAD_LEFT = 44;
  const PAD_BOTTOM = 28;
  const barW = Math.max(16, Math.floor((W - PAD_LEFT - 8) / data.length - 6));
  const chartH = H - PAD_BOTTOM;

  // Y-axis ticks (4 ticks)
  const tickCount = 4;
  const ticks = Array.from({ length: tickCount + 1 }, (_, i) =>
    Math.round((max / tickCount) * i * 10) / 10
  );

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} style={{ overflow: "visible" }}>
      {/* Y grid + labels (token: border/muted) */}
      {ticks.map((tick) => {
        const y = chartH - (tick / max) * chartH;
        return (
          <g key={tick}>
            <line
              x1={PAD_LEFT} x2={W} y1={y} y2={y}
              className="text-border" stroke="currentColor"
              strokeWidth={tick === 0 ? 1.5 : 0.75}
              strokeDasharray={tick === 0 ? "none" : "3,3"}
            />
            <text x={PAD_LEFT - 4} y={y + 4} textAnchor="end" fontSize={9} className="fill-muted">{tick}</text>
          </g>
        );
      })}

      {/* Bars (token: currentColor via colorClass) */}
      <g className={colorClass}>
        {data.map((row, i) => {
          const val = row[kpiKey] ?? 0;
          const barH = (val / max) * chartH;
          const x = PAD_LEFT + i * ((W - PAD_LEFT) / data.length) + ((W - PAD_LEFT) / data.length - barW) / 2;
          const y = chartH - barH;
          const isLast = i === data.length - 1;
          return (
            <g key={row.period}>
              <rect x={x} y={y} width={barW} height={barH} rx={3} fill="currentColor" opacity={isLast ? 1 : 0.5} />
              {val > 0 && (
                <text x={x + barW / 2} y={y - 3} textAnchor="middle" fontSize={9} fill="currentColor" fontWeight="600">
                  {kpiKey === "farrowing_rate" ? `${val.toFixed(1)}%` : val.toFixed(1)}
                </text>
              )}
              <text x={x + barW / 2} y={chartH + 14} textAnchor="middle" fontSize={9} className="fill-muted">
                {row.period.slice(5)}
              </text>
            </g>
          );
        })}
      </g>
    </svg>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

type KpiItem = (typeof KPI_LIST)[number];

const PERIOD_PRESETS = [3, 6, 12] as const;

export default function ReportsPage() {
  const t = useTranslations("reports");
  const farmId = useAuthStore((s) => s.activeFarmId);
  const [trendKpi, setTrendKpi] = useState<KpiKey>("psy");
  const [months, setMonths] = useState<number>(6);
  const [view, setView] = useState<"chart" | "table">("chart");

  // psy/npd는 약어 그대로, farrowing_rate만 번역 키 사용
  const kpiLabel = (k: KpiItem) => ("labelKey" in k ? t(k.labelKey) : k.label);
  const kpiUnit = (k: KpiItem) => t(k.unitKey);

  const { data: dashboard, isLoading } = useQuery({
    queryKey: queryKeys.kpi.dashboard(farmId ?? ""),
    queryFn: () => kpiApi.dashboard(farmId!),
    enabled: !!farmId,
  });

  // 백엔드 trend는 3개 KPI를 항상 함께 반환(kpi 파라미터 무시) → query key에서 trendKpi 제외해
  // 탭 전환 시 동일 데이터 재요청 방지(M1). 차트/테이블이 클라에서 trendKpi로 골라 표시.
  const { data: trend = [] } = useQuery({
    queryKey: ["kpi", "trend", farmId, months],
    queryFn: () => kpiApi.trend(farmId!, trendKpi, months),
    enabled: !!farmId,
  });

  const activeKpi = KPI_LIST.find((k) => k.key === trendKpi)!;

  // 현재 추세 데이터를 CSV로 내려받기 (의존성 없이 직접 생성).
  // 화면 테이블과 동일하게 3개 KPI 전부 + 1자리 포맷으로 내보낸다(H2: 컬럼 누락/생키 헤더 수정).
  const exportCsv = () => {
    if (trend.length === 0) return;
    const header = [t("colPeriod"), "PSY", "NPD", `${t("kpiFarrowingRate")} (%)`];
    const rows = buildReproCsvRows(trend);
    const csv = [header, ...rows]
      .map((cols) => cols.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(","))
      .join("\r\n");
    const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const start = trend[0]?.period ?? "";
    const end = trend[trend.length - 1]?.period ?? "";
    a.href = url;
    a.download = `pigos_report_${farmId}_${start}_${end}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!farmId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text3">{t("selectFarm")}</p>
      </div>
    );
  }

  return (
    <div className="p-7 max-w-4xl">
      <ReportsTabs />
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-[22px] font-extrabold tracking-tight">{t("title")}</h1>
          <p className="text-xs text-text3 mt-0.5">
            {dashboard ? t("asOf", { date: dashboard.as_of.slice(0, 10) }) : t("summary")}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* 기간 프리셋 */}
          <div className="flex border border-border rounded-lg overflow-hidden">
            {PERIOD_PRESETS.map((m) => (
              <button
                key={m}
                onClick={() => setMonths(m)}
                className={`px-3 py-1.5 text-xs font-semibold transition ${
                  months === m ? "bg-primary text-white" : "bg-background text-text3 hover:bg-border"
                }`}
              >
                {t("monthsPreset", { n: m })}
              </button>
            ))}
          </div>
          <button
            onClick={exportCsv}
            disabled={trend.length === 0}
            className="text-xs font-semibold text-text3 border border-border rounded-lg px-3 py-1.5 hover:bg-border transition disabled:opacity-50"
          >
            {t("exportCsv")}
          </button>
        </div>
      </div>

      {/* KPI 요약 카드 */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        {KPI_LIST.map((k) => {
          const { key, colorClass } = k;
          const raw = dashboard?.[key as keyof typeof dashboard];
          const value = typeof raw === "number" ? raw : null;
          const selected = trendKpi === key;
          return (
            <div
              key={key}
              className={`bg-surface border rounded-2xl p-5 cursor-pointer transition ${selected ? "border-primary" : "border-border hover:border-primary/40"}`}
              onClick={() => setTrendKpi(key)}
            >
              <div className="text-xs font-semibold text-text3 mb-1">{kpiLabel(k)}</div>
              {isLoading ? (
                <div className="h-8 bg-border rounded animate-pulse w-16" />
              ) : (
                <div className={`text-3xl font-extrabold font-mono tracking-tight ${selected ? colorClass : "text-text"}`}>
                  {value != null ? value.toFixed(1) : "-"}
                  <span className="text-sm font-normal text-text3 ml-1">{kpiUnit(k)}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 모돈 현황 */}
      {dashboard && (
        <div className="bg-surface border border-border rounded-2xl p-5 mb-6">
          <h2 className="text-sm font-bold text-text mb-4">{t("sowStatusTitle")}</h2>
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: t("activeSows"), value: dashboard.active_sows },
              { label: t("pregnant"),   value: dashboard.gestating },
              { label: t("lactating"),  value: dashboard.lactating },
              { label: t("weaned"),     value: dashboard.weaned },
            ].map(({ label, value }) => (
              <div key={label} className="text-center">
                <div className="text-2xl font-extrabold font-mono text-text">{value}</div>
                <div className="text-xs text-text3 mt-0.5">{label} ({t("unitHead")})</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 추세 — Chart / Table 전환 */}
      <div className="bg-surface border border-border rounded-2xl p-5">
        {/* Toolbar */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold text-text">{t("trendTitle")}</h2>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full border border-border text-text3">
              {kpiLabel(activeKpi)}
            </span>
          </div>
          <div className="flex gap-1">
            {/* KPI 탭 */}
            {KPI_LIST.map((k) => (
              <button
                key={k.key}
                onClick={() => setTrendKpi(k.key)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                  trendKpi === k.key
                    ? "bg-primary text-white"
                    : "bg-background border border-border text-text3 hover:bg-border"
                }`}
              >
                {kpiLabel(k)}
              </button>
            ))}
            {/* View 전환 */}
            <div className="ml-2 flex border border-border rounded-lg overflow-hidden">
              {(["chart", "table"] as const).map((v) => (
                <button
                  key={v}
                  onClick={() => setView(v)}
                  className={`px-2.5 py-1 text-xs font-semibold transition ${
                    view === v ? "bg-primary text-white" : "bg-background text-text3 hover:bg-border"
                  }`}
                >
                  {v === "chart" ? t("viewChart") : t("viewTable")}
                </button>
              ))}
            </div>
          </div>
        </div>

        {trend.length === 0 ? (
          <div className="py-8 text-center text-sm text-text3">{t("noTrend")}</div>
        ) : view === "chart" ? (
          <div className="px-2">
            <BarChart data={trend} kpiKey={trendKpi} colorClass={activeKpi.colorClass} />
            <div className="flex items-center gap-1.5 mt-3 text-xs text-text3">
              <span className={`inline-block w-3 h-3 rounded-sm bg-current ${activeKpi.colorClass}`} />
              {kpiLabel(activeKpi)} ({kpiUnit(activeKpi)})
              <span className="ml-2 opacity-60">{t("legendRecent")}</span>
            </div>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-2 text-xs font-semibold text-text3">{t("colPeriod")}</th>
                <th className="text-right py-2 text-xs font-semibold text-text3">PSY</th>
                <th className="text-right py-2 text-xs font-semibold text-text3">NPD</th>
                <th className="text-right py-2 text-xs font-semibold text-text3">{t("kpiFarrowingRate")}</th>
              </tr>
            </thead>
            <tbody>
              {trend.map((row, i) => (
                <tr key={row.period} className={i < trend.length - 1 ? "border-b border-border" : ""}>
                  <td className="py-2.5 font-mono text-xs text-text2">{row.period}</td>
                  <td className="py-2.5 text-right font-mono text-text">
                    {row.psy != null ? row.psy.toFixed(1) : "-"}
                  </td>
                  <td className="py-2.5 text-right font-mono text-text">
                    {row.npd != null ? row.npd.toFixed(1) : "-"}
                  </td>
                  <td className="py-2.5 text-right font-mono text-text">
                    {row.farrowing_rate != null ? `${row.farrowing_rate.toFixed(1)}%` : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

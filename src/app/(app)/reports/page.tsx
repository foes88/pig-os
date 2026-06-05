"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { kpiApi } from "@/lib/api/endpoints/kpi";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";

const KPI_LIST = [
  { key: "psy",           label: "PSY",    unit: "두/모돈/년", good: "high" },
  { key: "npd",           label: "NPD",    unit: "일",         good: "low"  },
  { key: "farrowing_rate", label: "분만율", unit: "%",          good: "high" },
] as const;

type KpiKey = (typeof KPI_LIST)[number]["key"];

export default function ReportsPage() {
  const farmId = useAuthStore((s) => s.activeFarmId);
  const [trendKpi, setTrendKpi] = useState<KpiKey>("psy");

  const { data: dashboard, isLoading } = useQuery({
    queryKey: queryKeys.kpi.dashboard(farmId ?? ""),
    queryFn: () => kpiApi.dashboard(farmId!),
    enabled: !!farmId,
  });

  const { data: trend = [] } = useQuery({
    queryKey: ["kpi", "trend", farmId, trendKpi],
    queryFn: () => kpiApi.trend(farmId!, trendKpi, 6),
    enabled: !!farmId,
  });

  if (!farmId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text3">농장을 선택해주세요.</p>
      </div>
    );
  }

  return (
    <div className="p-7 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-[22px] font-extrabold tracking-tight">보고서</h1>
          <p className="text-xs text-text3 mt-0.5">
            {dashboard ? `기준일: ${dashboard.as_of.slice(0, 10)}` : "KPI 성과 요약"}
          </p>
        </div>
        <button className="text-xs font-semibold text-text3 border border-border rounded-lg px-3 py-1.5 hover:bg-border transition">
          Excel 내보내기
        </button>
      </div>

      {/* KPI 요약 카드 */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        {KPI_LIST.map(({ key, label, unit, good }) => {
          const raw = dashboard?.[key as keyof typeof dashboard];
          const value = typeof raw === "number" ? raw : null;
          return (
            <div key={key} className="bg-surface border border-border rounded-2xl p-5">
              <div className="text-xs font-semibold text-text3 mb-1">{label}</div>
              {isLoading ? (
                <div className="h-8 bg-border rounded animate-pulse w-16" />
              ) : (
                <div className="text-3xl font-extrabold font-mono tracking-tight text-text">
                  {value != null ? value.toFixed(1) : "-"}
                  <span className="text-sm font-normal text-text3 ml-1">{unit}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 모돈 현황 */}
      {dashboard && (
        <div className="bg-surface border border-border rounded-2xl p-5 mb-6">
          <h2 className="text-sm font-bold text-text mb-4">모돈 현황</h2>
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: "활성 모돈", value: dashboard.active_sows, unit: "두" },
              { label: "임신",      value: dashboard.gestating,   unit: "두" },
              { label: "포유",      value: dashboard.lactating,   unit: "두" },
              { label: "이유",      value: dashboard.weaned,      unit: "두" },
            ].map(({ label, value, unit }) => (
              <div key={label} className="text-center">
                <div className="text-2xl font-extrabold font-mono text-text">{value}</div>
                <div className="text-xs text-text3 mt-0.5">{label} ({unit})</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 추세 */}
      <div className="bg-surface border border-border rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-bold text-text">6개월 추세</h2>
          <div className="flex gap-1">
            {KPI_LIST.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setTrendKpi(key)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                  trendKpi === key
                    ? "bg-primary text-white"
                    : "bg-background border border-border text-text3 hover:bg-border"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {trend.length === 0 ? (
          <div className="py-8 text-center text-sm text-text3">
            추세 데이터가 없습니다
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-2 text-xs font-semibold text-text3">기간</th>
                <th className="text-right py-2 text-xs font-semibold text-text3">PSY</th>
                <th className="text-right py-2 text-xs font-semibold text-text3">NPD</th>
                <th className="text-right py-2 text-xs font-semibold text-text3">분만율</th>
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

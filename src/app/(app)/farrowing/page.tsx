"use client";

import { useQuery } from "@tanstack/react-query";
import { eventsApi } from "@/lib/api/endpoints/events";
import { sowsApi } from "@/lib/api/endpoints/sows";
import { kpiApi } from "@/lib/api/endpoints/kpi";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import type { Farrowing } from "@/types/api.types";

const DIFFICULTY_LABEL: Record<string, string> = {
  NORMAL: "정상",
  ASSISTED: "도움",
  DIFFICULT: "난산",
};

export default function FarrowingPage() {
  const farmId = useAuthStore((s) => s.activeFarmId);

  const { data: kpi } = useQuery({
    queryKey: queryKeys.kpi.dashboard(farmId ?? ""),
    queryFn: () => kpiApi.dashboard(farmId!),
    enabled: !!farmId,
  });

  const { data: farrowings = [], isLoading } = useQuery({
    queryKey: ["farrowings", farmId],
    queryFn: () => eventsApi.farrowings.list(farmId!),
    enabled: !!farmId,
  });

  const { data: sowData } = useQuery({
    queryKey: queryKeys.sows.list(farmId ?? "", { status: "LACTATING" }),
    queryFn: () => sowsApi.list(farmId!, { status: "LACTATING", per_page: 200 }),
    enabled: !!farmId,
  });

  if (!farmId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text3">농장을 선택해주세요.</p>
      </div>
    );
  }

  const lactating = sowData?.items ?? [];
  const recent = [...farrowings]
    .sort((a, b) => b.farrowing_date.localeCompare(a.farrowing_date))
    .slice(0, 30);

  const avgBornAlive =
    farrowings.length > 0
      ? (farrowings.reduce((s, f) => s + f.born_alive, 0) / farrowings.length).toFixed(1)
      : "-";
  const avgStillborn =
    farrowings.length > 0
      ? (farrowings.reduce((s, f) => s + f.stillborn, 0) / farrowings.length).toFixed(1)
      : "-";

  return (
    <div className="p-7">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-[22px] font-extrabold tracking-tight">분만사</h1>
          <p className="text-xs text-text3 mt-0.5">
            포유 중 {kpi?.lactating ?? 0}두 · 분만율 {kpi?.farrowing_rate != null ? `${kpi.farrowing_rate.toFixed(1)}%` : "-"}
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {[
          { label: "포유 모돈", value: String(kpi?.lactating ?? 0), unit: "두", color: "text-success" },
          { label: "분만율", value: kpi?.farrowing_rate != null ? kpi.farrowing_rate.toFixed(1) : "-", unit: "%", color: "text-primary" },
          { label: "평균 실산자", value: avgBornAlive, unit: "두", color: "text-text" },
          { label: "평균 사산", value: avgStillborn, unit: "두", color: "text-danger" },
        ].map(({ label, value, unit, color }) => (
          <div key={label} className="bg-surface border border-border rounded-2xl p-4">
            <div className="text-xs text-text3 mb-1">{label}</div>
            <div className={`text-2xl font-extrabold font-mono tracking-tight ${color}`}>
              {value}<span className="text-sm font-normal text-text3 ml-1">{unit}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid md:grid-cols-2 gap-5">
        {/* 포유 중 모돈 */}
        <div>
          <h2 className="text-sm font-bold text-text mb-3">포유 중 모돈 ({lactating.length}두)</h2>
          {lactating.length === 0 ? (
            <div className="bg-surface border border-border rounded-2xl p-8 text-center text-sm text-text3">
              포유 중인 모돈이 없습니다
            </div>
          ) : (
            <div className="bg-surface border border-border rounded-2xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left px-4 py-2.5 text-xs font-semibold text-text3">이표</th>
                    <th className="text-center px-4 py-2.5 text-xs font-semibold text-text3">산차</th>
                  </tr>
                </thead>
                <tbody>
                  {lactating.slice(0, 15).map((sow, i) => (
                    <tr key={sow.id} className={i < lactating.length - 1 ? "border-b border-border" : ""}>
                      <td className="px-4 py-2.5 font-mono font-semibold text-text">{sow.ear_tag}</td>
                      <td className="px-4 py-2.5 text-center text-text3">{sow.parity}산</td>
                    </tr>
                  ))}
                  {lactating.length > 15 && (
                    <tr>
                      <td colSpan={2} className="px-4 py-2 text-xs text-text3 text-center">
                        외 {lactating.length - 15}두
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* 최근 분만 기록 */}
        <div>
          <h2 className="text-sm font-bold text-text mb-3">최근 분만 기록</h2>
          {isLoading ? (
            <div className="bg-surface border border-border rounded-2xl p-8 text-center text-sm text-text3">
              로딩 중...
            </div>
          ) : recent.length === 0 ? (
            <div className="bg-surface border border-border rounded-2xl p-8 text-center text-sm text-text3">
              분만 기록이 없습니다
            </div>
          ) : (
            <div className="bg-surface border border-border rounded-2xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left px-4 py-2.5 text-xs font-semibold text-text3">날짜</th>
                    <th className="text-center px-4 py-2.5 text-xs font-semibold text-text3">실산</th>
                    <th className="text-center px-4 py-2.5 text-xs font-semibold text-text3">사산</th>
                    <th className="text-center px-4 py-2.5 text-xs font-semibold text-text3">총산</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.map((f: Farrowing, i) => (
                    <tr key={f.id} className={i < recent.length - 1 ? "border-b border-border" : ""}>
                      <td className="px-4 py-2.5 font-mono text-xs text-text2">{f.farrowing_date}</td>
                      <td className="px-4 py-2.5 text-center font-bold text-success">{f.born_alive}</td>
                      <td className="px-4 py-2.5 text-center text-danger">{f.stillborn}</td>
                      <td className="px-4 py-2.5 text-center text-text3">{f.total_born}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

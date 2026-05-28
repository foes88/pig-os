"use client";

import { useQuery } from "@tanstack/react-query";
import { Sidebar } from "@/components/Sidebar";
import { kpiApi } from "@/lib/api/endpoints/kpi";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import type { Alert } from "@/types/api.types";

const SEVERITY_STYLE: Record<string, { cls: string; icon: string }> = {
  OK:       { cls: "bg-green-50 border-green-200 text-green-700", icon: "✓" },
  INFO:     { cls: "bg-blue-50 border-blue-200 text-blue-700",    icon: "ℹ" },
  WARNING:  { cls: "bg-amber-50 border-amber-200 text-amber-700", icon: "⚠" },
  CRITICAL: { cls: "bg-red-50 border-red-200 text-red-700",       icon: "🚨" },
};

export default function KpiPage() {
  const farmId = useAuthStore((s) => s.activeFarmId);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: queryKeys.kpi.dashboard(farmId ?? ""),
    queryFn: () => kpiApi.dashboard(farmId!),
    enabled: !!farmId,
    refetchInterval: 5 * 60 * 1000,
  });

  if (!farmId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text3">농장을 선택해주세요.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="ml-[220px] p-7">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[22px] font-extrabold tracking-tight">KPI 현황</h1>
            {data && (
              <p className="text-xs text-text3 mt-0.5">
                기준일: {data.as_of.slice(0, 10)} &nbsp;·&nbsp; 활성 모돈 {data.active_sows}두
              </p>
            )}
          </div>
          <button
            onClick={() => refetch()}
            className="text-xs text-text3 border border-border rounded-lg px-3 py-1.5 hover:bg-border transition"
          >
            새로고침
          </button>
        </div>

        {isLoading && (
          <div className="text-center text-text3 py-20">KPI 계산 중...</div>
        )}

        {isError && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
            데이터를 불러오지 못했습니다. API 서버 연결을 확인해주세요.
          </div>
        )}

        {data && (
          <>
            {/* Core KPI cards */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <KpiCard
                label="PSY"
                desc="연간 모돈두당 이유두수"
                value={data.psy != null ? data.psy.toFixed(1) : "-"}
                benchmark="≥ 28.0"
                good={data.psy != null && data.psy >= 28}
              />
              <KpiCard
                label="NPD"
                desc="비생산일수"
                value={data.npd != null ? data.npd.toFixed(1) + "일" : "-"}
                benchmark="≤ 35일"
                good={data.npd != null && data.npd <= 35}
                invert
              />
              <KpiCard
                label="분만율"
                desc="교배 대비 분만 비율"
                value={data.farrowing_rate != null ? (data.farrowing_rate * 100).toFixed(1) + "%" : "-"}
                benchmark="≥ 90%"
                good={data.farrowing_rate != null && data.farrowing_rate >= 0.9}
              />
            </div>

            {/* Herd status */}
            <div className="grid grid-cols-4 gap-3 mb-6">
              <HerdCard label="임신" value={data.gestating} color="blue" />
              <HerdCard label="포유" value={data.lactating} color="green" />
              <HerdCard label="이유/공태" value={data.weaned} color="amber" />
              <HerdCard label="활성 전체" value={data.active_sows} color="slate" />
            </div>

            {/* Alerts */}
            {data.alerts.length > 0 && (
              <div>
                <h2 className="text-sm font-bold mb-3">Rule Engine 알림</h2>
                <div className="space-y-2">
                  {data.alerts.map((alert, i) => (
                    <AlertRow key={i} alert={alert} />
                  ))}
                </div>
              </div>
            )}

            {data.alerts.length === 0 && (
              <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-sm text-green-700">
                ✓ 현재 Rule Engine 알림 없음 — 모든 KPI 정상 범위
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

function KpiCard({
  label, desc, value, benchmark, good, invert = false,
}: {
  label: string; desc: string; value: string;
  benchmark: string; good: boolean; invert?: boolean;
}) {
  const color = value === "-" ? "text-text3" : good ? "text-success" : "text-danger";
  return (
    <div className="bg-surface border border-border rounded-xl p-5">
      <div className="text-xs text-text3 mb-1">{desc}</div>
      <div className="text-[11px] font-bold text-text2 mb-2 uppercase tracking-wide">{label}</div>
      <div className={`font-mono text-3xl font-extrabold ${color}`}>{value}</div>
      <div className="text-[10px] text-text3 mt-2">목표: {benchmark}</div>
    </div>
  );
}

function HerdCard({ label, value, color }: { label: string; value: number; color: string }) {
  const colors: Record<string, string> = {
    blue: "bg-blue-50 border-blue-100 text-blue-700",
    green: "bg-green-50 border-green-100 text-green-700",
    amber: "bg-amber-50 border-amber-100 text-amber-700",
    slate: "bg-slate-50 border-slate-200 text-slate-700",
  };
  return (
    <div className={`border rounded-xl p-4 ${colors[color] ?? colors.slate}`}>
      <div className="text-[10px] font-medium mb-1">{label}</div>
      <div className="font-mono text-2xl font-extrabold">{value}두</div>
    </div>
  );
}

function AlertRow({ alert }: { alert: Alert }) {
  const style = SEVERITY_STYLE[alert.severity] ?? SEVERITY_STYLE.INFO;
  return (
    <div className={`border rounded-xl px-4 py-3 flex items-start gap-3 ${style.cls}`}>
      <span className="font-bold text-base flex-shrink-0">{style.icon}</span>
      <div className="flex-1 min-w-0">
        <div className="text-xs font-semibold">{alert.kpi} — {alert.message}</div>
        {alert.current_value != null && (
          <div className="text-[10px] mt-0.5 opacity-75">
            현재 {alert.current_value.toFixed(1)} / 목표 {alert.target_value?.toFixed(1) ?? "-"}
          </div>
        )}
      </div>
      <span className="text-[9px] font-bold opacity-60 flex-shrink-0">{alert.rule_id}</span>
    </div>
  );
}

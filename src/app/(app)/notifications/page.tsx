"use client";

import { useQuery } from "@tanstack/react-query";
import { kpiApi } from "@/lib/api/endpoints/kpi";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import type { Alert } from "@/types/api.types";

const SEVERITY_STYLES: Record<Alert["severity"], { bg: string; dot: string; label: string }> = {
  CRITICAL: { bg: "bg-red-50 border-red-200",   dot: "bg-danger",   label: "위험" },
  WARNING:  { bg: "bg-amber-50 border-amber-200", dot: "bg-warning",  label: "주의" },
  INFO:     { bg: "bg-blue-50 border-blue-200",   dot: "bg-primary",  label: "정보" },
  OK:       { bg: "bg-surface border-border",     dot: "bg-success",  label: "정상" },
};

export default function NotificationsPage() {
  const farmId = useAuthStore((s) => s.activeFarmId);

  const { data: dashboard, isLoading } = useQuery({
    queryKey: queryKeys.kpi.dashboard(farmId ?? ""),
    queryFn: () => kpiApi.dashboard(farmId!),
    enabled: !!farmId,
  });

  const alerts = dashboard?.alerts ?? [];
  const active = alerts.filter((a) => a.severity !== "OK");
  const ok = alerts.filter((a) => a.severity === "OK");

  if (!farmId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text3">농장을 선택해주세요.</p>
      </div>
    );
  }

  return (
    <div className="p-7 max-w-2xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-[22px] font-extrabold tracking-tight">알림</h1>
        <p className="text-xs text-text3 mt-0.5">KPI 기반 자동 알림</p>
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-border rounded-2xl animate-pulse" />
          ))}
        </div>
      )}

      {!isLoading && alerts.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 text-text3">
          <span className="text-5xl mb-4">🔔</span>
          <p className="font-semibold">알림이 없습니다</p>
          <p className="text-xs mt-1">KPI가 정상 범위이면 알림이 발생하지 않습니다.</p>
        </div>
      )}

      {/* Active alerts */}
      {active.length > 0 && (
        <section className="mb-6">
          <div className="text-[11px] font-bold text-faint uppercase tracking-widest mb-2">
            주의 필요 ({active.length})
          </div>
          <div className="space-y-2">
            {active.map((alert) => {
              const s = SEVERITY_STYLES[alert.severity];
              return (
                <div key={alert.rule_id} className={`border rounded-2xl px-4 py-3.5 ${s.bg}`}>
                  <div className="flex items-start gap-3">
                    <span className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${s.dot}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-[10px] font-bold uppercase tracking-wide text-text3">
                          {alert.kpi}
                        </span>
                        <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded bg-white/70 text-text3">
                          {s.label}
                        </span>
                      </div>
                      <p className="text-sm font-semibold text-text leading-snug">{alert.message}</p>
                      {alert.current_value != null && alert.target_value != null && (
                        <p className="text-xs text-text3 mt-0.5 font-mono">
                          현재 {alert.current_value.toFixed(2)} → 목표 {alert.target_value.toFixed(2)}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* OK alerts */}
      {ok.length > 0 && (
        <section>
          <div className="text-[11px] font-bold text-faint uppercase tracking-widest mb-2">
            정상 ({ok.length})
          </div>
          <div className="space-y-1.5">
            {ok.map((alert) => (
              <div key={alert.rule_id} className="border border-border rounded-2xl px-4 py-3 flex items-center gap-3">
                <span className="w-2 h-2 rounded-full bg-success flex-shrink-0" />
                <div>
                  <span className="text-[10px] font-bold text-text3 uppercase tracking-wide mr-2">{alert.kpi}</span>
                  <span className="text-sm text-text2">{alert.message}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

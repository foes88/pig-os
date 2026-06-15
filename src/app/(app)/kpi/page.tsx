"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
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
  const t = useTranslations("kpi");
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
        <p className="text-text3">{t("selectFarm")}</p>
      </div>
    );
  }

  return (
    <div className="p-7">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[22px] font-extrabold tracking-tight">{t("pageTitle")}</h1>
            {data && (
              <p className="text-xs text-text3 mt-0.5">
                {t("asOfActive", { date: data.as_of.slice(0, 10), n: data.active_sows })}
              </p>
            )}
          </div>
          <button
            onClick={() => refetch()}
            className="text-xs text-text3 border border-border rounded-lg px-3 py-1.5 hover:bg-border transition"
          >
            {t("refresh")}
          </button>
        </div>

        {isLoading && (
          <div className="text-center text-text3 py-20">{t("calculating")}</div>
        )}

        {isError && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
            {t("loadError")}
          </div>
        )}

        {data && (
          <>
            {/* Core KPI cards — 목표값은 국가별 벤치마크(API)에서, 없으면 폴백 */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              {(() => {
                const psyT = data.benchmarks?.PSY?.target ?? 28;
                const npdT = data.benchmarks?.NPD?.target ?? 35;
                const frT = data.benchmarks?.FARROWING_RATE?.target ?? 90;
                return (
                  <>
                    <KpiCard
                      label="PSY"
                      desc={t("psyDesc")}
                      value={data.psy != null ? data.psy.toFixed(1) : "-"}
                      benchmark={`≥ ${psyT}`}
                      good={data.psy != null && data.psy >= psyT}
                    />
                    <KpiCard
                      label="NPD"
                      desc={t("npdDesc")}
                      value={data.npd != null ? data.npd.toFixed(1) + t("daysUnit") : "-"}
                      benchmark={`≤ ${npdT}${t("daysUnit")}`}
                      good={data.npd != null && data.npd <= npdT}
                      invert
                    />
                    <KpiCard
                      label={t("frLabel")}
                      desc={t("frDesc")}
                      value={data.farrowing_rate != null ? (data.farrowing_rate * 100).toFixed(1) + "%" : "-"}
                      benchmark={`≥ ${frT}%`}
                      good={data.farrowing_rate != null && data.farrowing_rate * 100 >= frT}
                    />
                  </>
                );
              })()}
            </div>

            {/* Herd status */}
            <div className="grid grid-cols-4 gap-3 mb-6">
              <HerdCard label={t("herdPregnant")} value={data.gestating} color="blue" unit={t("headUnit")} />
              <HerdCard label={t("herdLactating")} value={data.lactating} color="green" unit={t("headUnit")} />
              <HerdCard label={t("herdWeanedOpen")} value={data.weaned} color="amber" unit={t("headUnit")} />
              <HerdCard label={t("herdActiveTotal")} value={data.active_sows} color="slate" unit={t("headUnit")} />
            </div>

            {/* Alerts */}
            {data.alerts.length > 0 && (
              <div>
                <h2 className="text-sm font-bold mb-3">{t("ruleAlerts")}</h2>
                <div className="space-y-2">
                  {data.alerts.map((alert, i) => (
                    <AlertRow key={i} alert={alert} />
                  ))}
                </div>
              </div>
            )}

            {data.alerts.length === 0 && (
              <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-sm text-green-700">
                {t("noAlerts")}
              </div>
            )}
          </>
        )}
    </div>
  );
}

function KpiCard({
  label, desc, value, benchmark, good, invert = false,
}: {
  label: string; desc: string; value: string;
  benchmark: string; good: boolean; invert?: boolean;
}) {
  const t = useTranslations("kpi");
  const color = value === "-" ? "text-text3" : good ? "text-success" : "text-danger";
  return (
    <div className="bg-surface border border-border rounded-xl p-5">
      <div className="text-xs text-text3 mb-1">{desc}</div>
      <div className="text-[11px] font-bold text-text2 mb-2 uppercase tracking-wide">{label}</div>
      <div className={`font-mono text-3xl font-extrabold ${color}`}>{value}</div>
      <div className="text-[10px] text-text3 mt-2">{t("target", { v: benchmark })}</div>
    </div>
  );
}

function HerdCard({ label, value, color, unit }: { label: string; value: number; color: string; unit: string }) {
  const colors: Record<string, string> = {
    blue: "bg-blue-50 border-blue-100 text-blue-700",
    green: "bg-green-50 border-green-100 text-green-700",
    amber: "bg-amber-50 border-amber-100 text-amber-700",
    slate: "bg-slate-50 border-slate-200 text-slate-700",
  };
  return (
    <div className={`border rounded-xl p-4 ${colors[color] ?? colors.slate}`}>
      <div className="text-[10px] font-medium mb-1">{label}</div>
      <div className="font-mono text-2xl font-extrabold">{value}{unit}</div>
    </div>
  );
}

function AlertRow({ alert }: { alert: Alert }) {
  const t = useTranslations("kpi");
  const style = SEVERITY_STYLE[alert.severity] ?? SEVERITY_STYLE.INFO;
  return (
    <div className={`border rounded-xl px-4 py-3 flex items-start gap-3 ${style.cls}`}>
      <span className="font-bold text-base flex-shrink-0">{style.icon}</span>
      <div className="flex-1 min-w-0">
        <div className="text-xs font-semibold">{alert.kpi} — {alert.message}</div>
        {alert.current_value != null && (
          <div className="text-[10px] mt-0.5 opacity-75">
            {t("currentTarget", { cur: alert.current_value.toFixed(1), tgt: alert.target_value?.toFixed(1) ?? "-" })}
          </div>
        )}
      </div>
      <span className="text-[9px] font-bold opacity-60 flex-shrink-0">{alert.rule_id}</span>
    </div>
  );
}

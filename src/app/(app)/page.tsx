"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Stat, AIBubble, AIAction, Card, PipeItem } from "@/components/ui";
import Link from "next/link";
import { kpiApi } from "@/lib/api/endpoints/kpi";
import { alertsApi } from "@/lib/api/endpoints/alerts";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import type { Alert } from "@/types/api.types";

const SEVERITY_STYLE: Record<string, { cls: string; icon: string }> = {
  OK:       { cls: "bg-green-50 border-green-200", icon: "✓" },
  INFO:     { cls: "bg-blue-50 border-blue-200",   icon: "ℹ" },
  WARNING:  { cls: "bg-amber-50 border-amber-200", icon: "⚠" },
  CRITICAL: { cls: "bg-red-50 border-red-200",     icon: "🚨" },
};

export default function Dashboard() {
  const t = useTranslations("dashboard");
  const farmId = useAuthStore((s) => s.activeFarmId);
  const user   = useAuthStore((s) => s.user);

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.kpi.dashboard(farmId ?? ""),
    queryFn:  () => kpiApi.dashboard(farmId!),
    enabled:  !!farmId,
    refetchInterval: 5 * 60 * 1000,
  });

  const { data: overdueData } = useQuery({
    queryKey: queryKeys.alerts.overdue(farmId ?? ""),
    queryFn: () => alertsApi.overdue(farmId!),
    enabled: !!farmId,
  });
  const { data: cullData } = useQuery({
    queryKey: queryKeys.alerts.cullCandidates(farmId ?? ""),
    queryFn: () => alertsApi.cullCandidates(farmId!),
    enabled: !!farmId,
  });

  const farmName = user?.name ?? "My Farm";

  return (
    <div className="p-7">
      {/* Header */}
      <div className="flex items-center justify-between mb-7">
        <div>
          <h1 className="text-[22px] font-extrabold tracking-tight flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse shadow-[0_0_8px_var(--color-primary)]" />
            {t("title")}
          </h1>
          <p className="text-xs text-text3">
            {farmName}
            {data && ` · ${data.active_sows}${t("unitHead")} · ${t("subtitleRealtime")}`}
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-primary-soft text-primary border border-primary/20 rounded-full text-xs font-semibold">
          🧠 {t("aiActive")}
        </span>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="text-center py-20 text-text3 text-sm">{t("loading")}</div>
      )}

      {/* No farm */}
      {!farmId && (
        <div className="text-center py-20 text-text3 text-sm">{t("selectFarm")}</div>
      )}

      {data && (
        <>
          {/* Critical alerts */}
          {data.alerts.filter((a) => a.severity === "CRITICAL").map((alert, i) => (
            <AlertBanner key={i} alert={alert} />
          ))}

          {/* Stats */}
          <div className="grid grid-cols-4 gap-3 mb-6">
            <Stat
              label="PSY"
              value={data.psy != null ? data.psy.toFixed(1) : "-"}
              sub={data.psy != null ? (data.psy >= 28 ? t("met") : t("belowTarget")) : t("noData")}
              subType={data.psy != null && data.psy >= 28 ? "up" : "down"}
            />
            <Stat
              label={t("statNpd")}
              value={data.npd != null ? `${data.npd.toFixed(1)}${t("unitDays")}` : "-"}
              sub={data.npd != null ? (data.npd <= 35 ? t("belowOk") : t("aboveTarget")) : t("noData")}
              subType={data.npd != null && data.npd <= 35 ? "up" : "down"}
            />
            <Stat
              label={t("statFarrowingRate")}
              value={data.farrowing_rate != null ? `${(data.farrowing_rate * 100).toFixed(1)}%` : "-"}
              sub={data.farrowing_rate != null ? (data.farrowing_rate >= 0.9 ? t("met") : t("belowTarget")) : t("noData")}
              subType={data.farrowing_rate != null && data.farrowing_rate >= 0.9 ? "up" : "down"}
            />
            <Stat
              label={t("statAiAlerts")}
              value={String(data.alerts.length)}
              sub={t("severeWarn", {
                crit: data.alerts.filter((a) => a.severity === "CRITICAL").length,
                warn: data.alerts.filter((a) => a.severity === "WARNING").length,
              })}
              subType="ai"
              valueColor="var(--color-purple)"
            />
          </div>

          {/* Overdue management link */}
          <Link
            href="/alerts"
            className="flex items-center justify-between gap-3 border border-border rounded-xl px-4 py-3 mb-6 hover:border-primary transition bg-surface"
          >
            <div className="flex items-center gap-3">
              <span className="text-warning text-lg">⚠</span>
              <div>
                <div className="text-sm font-bold text-text">{t("overdueSows", { n: overdueData?.total ?? 0 })}</div>
                <div className="text-[11px] text-text3">{t("overdueSub", { n: cullData?.length ?? 0 })}</div>
              </div>
            </div>
            <span className="text-xs text-primary font-semibold">{t("viewAlerts")}</span>
          </Link>

          {/* Pipeline */}
          <div className="flex gap-1 mb-6">
            <PipeItem icon="💉" count={data.week_matings} name={t("pMating")} />
            <span className="flex items-center text-text3 text-xs">→</span>
            <PipeItem icon="🤰" count={data.gestating} name={t("pPregnant")} active />
            <span className="flex items-center text-text3 text-xs">→</span>
            <PipeItem icon="🐖" count={data.week_farrowings} name={t("pFarrowing")} />
            <span className="flex items-center text-text3 text-xs">→</span>
            <PipeItem icon="🍼" count={data.lactating} name={t("pLactating")} />
            <span className="flex items-center text-text3 text-xs">→</span>
            <PipeItem icon="🌱" count={data.week_weanings} name={t("pWeaning")} />
          </div>

          {/* Two column */}
          <div className="grid grid-cols-2 gap-4">
            {/* Left: Alerts */}
            <div>
              <Card title={`🧠 ${t("ruleAlerts")}`} badge={t("alertCount", { n: data.alerts.length })} badgeColor="purple" className="mb-4" children={<></>} />
              {data.alerts.length === 0 ? (
                <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-sm text-success">
                  {t("noAlertsAll")}
                </div>
              ) : (
                data.alerts.map((alert, i) => (
                  <AlertCard key={i} alert={alert} />
                ))
              )}
            </div>

            {/* Right: Herd status */}
            <div>
              <AIBubble label={t("aiBriefing")}>
                <p>
                  {t("briefPrefix")} <strong className="text-primary">{data.active_sows}{t("unitHead")}</strong>.
                  PSY <strong className="text-primary">{data.psy?.toFixed(1) ?? "-"}</strong>,
                  {" "}{t("briefMid")} <strong className="text-primary">{data.npd?.toFixed(1) ?? "-"}{t("unitDays")}</strong>.
                  {data.alerts.length > 0
                    ? ` ${t("briefAlertsSuffix", { n: data.alerts.length })}`
                    : ` ${t("briefOk")}`}
                </p>
              </AIBubble>

              <Card title={t("herdStatus")}>
                <table className="w-full text-xs">
                  <tbody>
                    {[
                      { label: t("herdPregnant"), value: data.gestating },
                      { label: t("herdLactating"), value: data.lactating },
                      { label: t("herdWeanedOpen"), value: data.weaned },
                      { label: t("herdActiveTotal"), value: data.active_sows },
                    ].map((row, i) => (
                      <tr key={i} className="border-b border-border">
                        <td className="py-2.5">{row.label}</td>
                        <td className="py-2.5 text-right font-mono font-bold">{row.value}{t("unitHead")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Card>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function AlertBanner({ alert }: { alert: Alert }) {
  const t = useTranslations("dashboard");
  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-5 flex items-start gap-3.5">
      <span className="text-xl flex-shrink-0">🚨</span>
      <div className="flex-1">
        <div className="text-[13px] font-bold text-danger mb-1">
          {alert.kpi} — {alert.message}
        </div>
        {alert.current_value != null && (
          <div className="text-xs text-text2">
            {t("currentTarget", {
              cur: alert.current_value.toFixed(1),
              tgt: alert.target_value?.toFixed(1) ?? "-",
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function AlertCard({ alert }: { alert: Alert }) {
  const t = useTranslations("dashboard");
  const style = SEVERITY_STYLE[alert.severity] ?? SEVERITY_STYLE.INFO;
  return (
    <div className={`border rounded-xl px-4 py-3 mb-2 flex items-start gap-3 ${style.cls}`}>
      <span className="font-bold flex-shrink-0">{style.icon}</span>
      <div className="flex-1 min-w-0">
        <div className="text-xs font-semibold">{alert.kpi} — {alert.message}</div>
        {alert.current_value != null && (
          <div className="text-[10px] mt-0.5 opacity-75">
            {t("currentTarget", {
              cur: alert.current_value.toFixed(1),
              tgt: alert.target_value?.toFixed(1) ?? "-",
            })}
          </div>
        )}
      </div>
      <span className="text-[9px] opacity-50 flex-shrink-0">{alert.rule_id}</span>
    </div>
  );
}

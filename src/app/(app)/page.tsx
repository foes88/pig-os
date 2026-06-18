"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { AIBubble, Card, PipeItem } from "@/components/ui";
import Link from "next/link";
import { AlertTriangle, Brain, CheckCircle2 } from "lucide-react";
import { SEVERITY_ICON, STAGE_ICON } from "@/lib/icons";
import { kpiApi } from "@/lib/api/endpoints/kpi";
import { alertsApi } from "@/lib/api/endpoints/alerts";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import { psyTier, npdTier, farrowingRateTier, TIER_STYLE, type KpiTier } from "@/lib/kpi/status";
import type { Alert } from "@/types/api.types";

const SEV_ORDER: Record<string, number> = { CRITICAL: 3, WARNING: 2, INFO: 1, OK: 0 };

// 동일 KPI 경고 중복 제거 — KPI별 최고 심각도 1개만.
function dedupeAlerts(alerts: Alert[]): Alert[] {
  const byKpi = new Map<string, Alert>();
  for (const a of alerts) {
    const key = a.kpi ?? a.rule_id ?? a.message;
    const cur = byKpi.get(key);
    if (!cur || (SEV_ORDER[a.severity] ?? 0) > (SEV_ORDER[cur.severity] ?? 0)) byKpi.set(key, a);
  }
  return [...byKpi.values()].sort((x, y) => (SEV_ORDER[y.severity] ?? 0) - (SEV_ORDER[x.severity] ?? 0));
}

// "PSY — PSY: 6.5" 중복 방지 — message가 이미 kpi를 포함하면 message만.
function alertTitle(a: Alert): string {
  const kpi = a.kpi ?? "";
  const msg = a.message ?? "";
  if (!kpi) return msg;
  if (!msg) return kpi;
  return msg.toUpperCase().includes(kpi.toUpperCase()) ? msg : `${kpi} — ${msg}`;
}

export default function Dashboard() {
  const t = useTranslations("dashboard");
  const farmId = useAuthStore((s) => s.activeFarmId);
  const user = useAuthStore((s) => s.user);

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.kpi.dashboard(farmId ?? ""),
    queryFn: () => kpiApi.dashboard(farmId!),
    enabled: !!farmId,
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
    <div className="p-7 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
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
          <Brain size={14} /> {t("aiActive")}
        </span>
      </div>

      {isLoading && <div className="text-center py-20 text-text3 text-sm">{t("loading")}</div>}
      {!farmId && <div className="text-center py-20 text-text3 text-sm">{t("selectFarm")}</div>}

      {data && (() => {
        const psyT = psyTier(data.psy);
        const npdT = npdTier(data.npd);
        const frT = farrowingRateTier(data.farrowing_rate);
        const alerts = dedupeAlerts(data.alerts ?? []);
        const topAlert = alerts[0];
        const insufficient: string[] = [];
        if (psyT === "insufficient") insufficient.push("PSY");
        if (npdT === "insufficient") insufficient.push(t("statNpd"));
        if (frT === "insufficient") insufficient.push(t("statFarrowingRate"));
        return (
          <>
            {/* ── AI 운영 진단 카드 (상단, 합성) ── */}
            <AiDiagnosis t={t} topAlert={topAlert} insufficient={insufficient} hasData={!!(data.active_sows || alerts.length)} />

            {/* ── KPI 4 cards ── */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
              <KpiCard t={t} label="PSY" tier={psyT} value={data.psy != null ? data.psy.toFixed(1) : ""} />
              <KpiCard t={t} label={t("statNpd")} tier={npdT} value={data.npd != null ? `${data.npd.toFixed(1)}${t("unitDays")}` : ""} />
              <KpiCard t={t} label={t("statFarrowingRate")} tier={frT} value={frT === "insufficient" ? "" : `${(data.farrowing_rate! * 100).toFixed(1)}%`} />
              <KpiCard
                t={t}
                label={t("statAiAlerts")}
                tier={topAlert ? (topAlert.severity === "CRITICAL" ? "critical" : topAlert.severity === "WARNING" ? "warning" : "good") : "good"}
                value={String(alerts.length)}
                rawTierLabel={t("severeWarn", {
                  crit: alerts.filter((a) => a.severity === "CRITICAL").length,
                  warn: alerts.filter((a) => a.severity === "WARNING").length,
                })}
              />
            </div>

            {/* 관리대상 모돈 */}
            <Link
              href="/alerts"
              className="flex items-center justify-between gap-3 border border-border rounded-xl px-4 py-3 mb-5 hover:border-primary transition bg-surface"
            >
              <div className="flex items-center gap-3">
                <AlertTriangle className="text-warning" size={20} />
                <div>
                  <div className="text-sm font-bold text-text">{t("overdueSows", { n: overdueData?.total ?? 0 })}</div>
                  <div className="text-[11px] text-text3">{t("overdueSub", { n: cullData?.length ?? 0 })}</div>
                </div>
              </div>
              <span className="text-xs text-primary font-semibold">{t("viewAlerts")}</span>
            </Link>

            {/* Pipeline */}
            <div className="flex gap-1 mb-6 overflow-x-auto">
              <PipeItem icon={<StageIcon stage="MATING" />} count={data.week_matings} name={t("pMating")} />
              <span className="flex items-center text-text3 text-xs">→</span>
              <PipeItem icon={<StageIcon stage="PREGNANT" />} count={data.gestating} name={t("pPregnant")} active />
              <span className="flex items-center text-text3 text-xs">→</span>
              <PipeItem icon={<StageIcon stage="FARROWING" />} count={data.week_farrowings} name={t("pFarrowing")} />
              <span className="flex items-center text-text3 text-xs">→</span>
              <PipeItem icon={<StageIcon stage="LACTATING" />} count={data.lactating} name={t("pLactating")} />
              <span className="flex items-center text-text3 text-xs">→</span>
              <PipeItem icon={<StageIcon stage="WEANING" />} count={data.week_weanings} name={t("pWeaning")} />
            </div>

            {/* 2-col: Rule Engine 알림 (dedup) | 군집 현황 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Card title={t("ruleAlerts")} badge={t("alertCount", { n: alerts.length })} badgeColor="purple" className="mb-3" children={<></>} />
                {alerts.length === 0 ? (
                  <div className="bg-bg2/40 border border-border rounded-xl p-5 flex items-start gap-3">
                    <CheckCircle2 className="text-success flex-shrink-0 mt-0.5" size={18} />
                    <p className="text-xs text-text2 leading-relaxed">{t("emptyAlertsGuide")}</p>
                  </div>
                ) : (
                  alerts.map((alert, i) => <AlertCard key={i} alert={alert} />)
                )}
              </div>

              <div>
                <Card title={t("herdStatus")}>
                  <table className="w-full text-xs">
                    <tbody>
                      {[
                        { label: t("herdPregnant"), value: data.gestating },
                        { label: t("herdLactating"), value: data.lactating },
                        { label: t("herdWeanedOpen"), value: data.weaned },
                        { label: t("herdActiveTotal"), value: data.active_sows },
                      ].map((row, i) => (
                        <tr key={i} className="border-b border-border last:border-0">
                          <td className="py-2.5 text-text2">{row.label}</td>
                          <td className="py-2.5 text-right font-mono font-bold">{row.value}{t("unitHead")}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Card>
              </div>
            </div>
          </>
        );
      })()}
    </div>
  );
}

// ── AI 운영 진단 (합성된 의사결정형 문구) ──
function AiDiagnosis({ t, topAlert, insufficient, hasData }: {
  t: ReturnType<typeof useTranslations>; topAlert?: Alert; insufficient: string[]; hasData: boolean;
}) {
  let body: string;
  if (!hasData) {
    body = t("aiDiagNoData");
  } else {
    const risk = topAlert ? topAlert.kpi : (insufficient.length ? t("riskDataQuality") : null);
    if (!risk) {
      body = t("aiDiagHealthy");
    } else {
      body = t("aiDiagRisk", { risk });
      if (insufficient.length) body += t("aiDiagInsufficient", { metrics: insufficient.join(", ") });
    }
  }
  return (
    <div className="rounded-2xl border border-primary/20 bg-primary-soft/40 p-5 mb-5 flex items-start gap-3.5">
      <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
        <Brain className="text-primary" size={18} />
      </div>
      <div className="flex-1">
        <div className="text-[11px] font-bold text-primary uppercase tracking-wider mb-1">{t("aiDiagTitle")}</div>
        <p className="text-[13px] text-text1 leading-relaxed">{body}</p>
      </div>
    </div>
  );
}

// ── KPI 카드 (4단계 tier) ──
function KpiCard({ t, label, tier, value, rawTierLabel }: {
  t: ReturnType<typeof useTranslations>; label: string; tier: KpiTier; value: string; rawTierLabel?: string;
}) {
  const s = TIER_STYLE[tier];
  const tierLabel = rawTierLabel ?? t(
    tier === "good" ? "tierGood" : tier === "warning" ? "tierWarning" : tier === "critical" ? "tierCritical" : "tierInsufficient",
  );
  return (
    <div className="rounded-2xl border border-border bg-surface px-4 py-3.5">
      <div className="text-[11px] text-text3 font-semibold">{label}</div>
      {tier === "insufficient" ? (
        <div className="text-base font-bold text-text3 mt-2">{t("dataInsufficient")}</div>
      ) : (
        <div className={`text-[28px] font-extrabold font-mono mt-1 tracking-tight ${s.text}`}>{value}</div>
      )}
      <div className={`inline-flex items-center gap-1.5 mt-2 px-2 py-0.5 rounded-md text-[10px] font-bold border ${s.chip}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />{tierLabel}
      </div>
    </div>
  );
}

function StageIcon({ stage }: { stage: keyof typeof STAGE_ICON }) {
  const Icon = STAGE_ICON[stage];
  return <Icon size={18} />;
}

function AlertCard({ alert }: { alert: Alert }) {
  const t = useTranslations("dashboard");
  const Icon = SEVERITY_ICON[alert.severity] ?? SEVERITY_ICON.INFO;
  const cls = alert.severity === "CRITICAL" ? "bg-red-50 border-red-200 text-danger"
    : alert.severity === "WARNING" ? "bg-amber-50 border-amber-200 text-warning"
    : "bg-blue-50 border-blue-200 text-primary";
  return (
    <div className={`border rounded-xl px-4 py-3 mb-2 flex items-start gap-3 ${cls}`}>
      <Icon size={16} className="flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <div className="text-xs font-semibold">{alertTitle(alert)}</div>
        {alert.current_value != null && (
          <div className="text-[10px] mt-0.5 opacity-75">
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

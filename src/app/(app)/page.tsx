"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Card, PipeItem } from "@/components/ui";
import Link from "next/link";
import { Brain, ArrowRight, CheckCircle2, ListTodo } from "lucide-react";
import { SEVERITY_ICON, STAGE_ICON } from "@/lib/icons";
import { kpiApi } from "@/lib/api/endpoints/kpi";
import { alertsApi } from "@/lib/api/endpoints/alerts";
import { tasksApi } from "@/lib/api/endpoints/tasks";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import { psyTier, npdTier, farrowingRateTier, TIER_STYLE, type KpiTier } from "@/lib/kpi/status";
import type { Alert, Task } from "@/types/api.types";

const SEV_ORDER: Record<string, number> = { CRITICAL: 3, WARNING: 2, INFO: 1, OK: 0 };

function dedupeAlerts(alerts: Alert[]): Alert[] {
  const byKpi = new Map<string, Alert>();
  for (const a of alerts) {
    const key = a.kpi ?? a.rule_id ?? a.message;
    const cur = byKpi.get(key);
    if (!cur || (SEV_ORDER[a.severity] ?? 0) > (SEV_ORDER[cur.severity] ?? 0)) byKpi.set(key, a);
  }
  return [...byKpi.values()].sort((x, y) => (SEV_ORDER[y.severity] ?? 0) - (SEV_ORDER[x.severity] ?? 0));
}

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

  const { data, isLoading, isError } = useQuery({
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
  const { data: tasks } = useQuery({
    queryKey: queryKeys.tasks.list(farmId ?? "", "OPEN"),
    queryFn: () => tasksApi.list(farmId!, "OPEN"),
    enabled: !!farmId,
  });

  const farmName = user?.name ?? "My Farm";

  return (
    <div className="p-7 max-w-5xl">
      <div className="flex items-center justify-between mb-5">
        <h1 className="text-[22px] font-extrabold tracking-tight flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-primary animate-pulse shadow-[0_0_8px_var(--color-primary)]" />
          {t("title")}
        </h1>
        <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-primary-soft text-primary border border-primary/20 rounded-full text-xs font-semibold">
          <Brain size={14} /> {t("aiActive")}
        </span>
      </div>

      {isLoading && <div className="text-center py-20 text-text3 text-sm">{t("loading")}</div>}
      {!farmId && <div className="text-center py-20 text-text3 text-sm">{t("selectFarm")}</div>}
      {isError && farmId && !isLoading && (
        <div className="rounded-2xl border border-danger/30 bg-danger/5 py-16 text-center">
          <p className="font-bold text-danger">{t("loadError")}</p>
          <p className="text-xs text-text3 mt-1">{t("loadErrorDesc")}</p>
        </div>
      )}

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
        const validCount = 3 - insufficient.length;
        const quality = Math.round((validCount / 3) * 100);
        const overdueTotal = overdueData?.total ?? 0;

        let verdict: string;
        if (!data.active_sows && !alerts.length) verdict = t("aiDiagNoData");
        else {
          const risk = topAlert ? topAlert.kpi : (insufficient.length ? t("riskDataQuality") : null);
          if (!risk) verdict = t("aiDiagHealthy");
          else {
            verdict = t("aiDiagRisk", { risk });
            if (insufficient.length) verdict += t("aiDiagInsufficient", { metrics: insufficient.join(", ") });
          }
        }

        return (
          <>
            {/* ── HERO: AI 운영 진단 ── */}
            <div className="rounded-2xl border border-primary/20 bg-gradient-to-br from-primary-soft/50 to-surface p-6 mb-5">
              <div className="flex items-start justify-between gap-4 mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <Brain className="text-primary" size={20} />
                  </div>
                  <div>
                    <div className="text-[11px] font-bold text-primary uppercase tracking-wider">{t("aiDiagTitle")}</div>
                    <div className="text-xs text-text3">{farmName} · {data.active_sows}{t("unitHead")}</div>
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  <div className="text-[10px] text-text3 font-semibold">{t("dataQualityLabel")}</div>
                  <div className={`text-xl font-extrabold font-mono ${quality >= 66 ? "text-success" : quality >= 33 ? "text-warning" : "text-danger"}`}>{quality}%</div>
                </div>
              </div>
              <p className="text-[15px] text-text1 leading-relaxed font-medium mb-3">{verdict}</p>
              {data.estimated_loss && data.estimated_loss.amount > 0 && (
                <div className="inline-flex items-center gap-2 mb-4 px-3 py-1.5 rounded-lg bg-danger/8 border border-danger/20">
                  <span className="text-[11px] font-semibold text-text3">{t("estLoss")}</span>
                  <span className="text-sm font-extrabold font-mono text-danger">
                    {data.estimated_loss.currency}{data.estimated_loss.amount.toLocaleString()}
                  </span>
                  <span className="text-[11px] text-text3">· {t("lostPigs", { n: data.estimated_loss.lost_pigs })}</span>
                  {data.estimated_loss.demo && (
                    <span className="text-[9px] font-bold bg-bg2 text-text3 rounded px-1 py-0.5">{t("demoBadge")}</span>
                  )}
                </div>
              )}
              <div className="flex gap-2 flex-wrap">
                <Link href="/record" className="inline-flex items-center gap-1.5 bg-primary text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-primary/90 transition">
                  {t("actionRecord")} <ArrowRight size={14} />
                </Link>
                {overdueTotal > 0 && (
                  <Link href="/alerts" className="inline-flex items-center gap-1.5 border border-border bg-surface text-text2 px-4 py-2 rounded-lg text-sm font-semibold hover:border-primary transition">
                    {t("actionAlerts", { n: overdueTotal })}
                  </Link>
                )}
              </div>
            </div>

            {/* ── 오늘 할 행동 ── */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2.5">
                <h2 className="text-sm font-bold flex items-center gap-2">
                  <ListTodo size={15} /> {t("todayActions")}
                  {!!tasks?.length && <span className="text-[10px] font-bold bg-primary/10 text-primary rounded-full px-1.5 py-0.5">{tasks.length}</span>}
                </h2>
                <Link href="/tasks" className="text-xs text-primary font-semibold">{t("viewAllTasks")} →</Link>
              </div>
              {!tasks?.length ? (
                <div className="bg-bg2/40 border border-border rounded-xl p-5 flex items-start gap-3">
                  <CheckCircle2 className="text-success flex-shrink-0 mt-0.5" size={18} />
                  <p className="text-xs text-text2 leading-relaxed">{t("noTasks")}</p>
                </div>
              ) : (
                <div className="space-y-1.5">
                  {tasks.slice(0, 5).map((task) => (
                    <TaskRow key={task.id} task={task} />
                  ))}
                </div>
              )}
            </div>

            {/* ── 보조: 핵심 지표 ── */}
            <div className="text-[11px] font-bold text-text3 uppercase tracking-widest mb-2">{t("kpiSummary")}</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
              <KpiCard t={t} label="PSY" tier={psyT} value={data.psy != null ? data.psy.toFixed(1) : ""} />
              <KpiCard t={t} label={t("statNpd")} tier={npdT} value={data.npd != null ? `${data.npd.toFixed(1)}${t("unitDays")}` : ""} />
              <KpiCard t={t} label={t("statFarrowingRate")} tier={frT} value={frT === "insufficient" ? "" : `${data.farrowing_rate!.toFixed(1)}%`} />
              <KpiCard
                t={t}
                label={t("statAiAlerts")}
                tier={topAlert ? (topAlert.severity === "CRITICAL" ? "critical" : topAlert.severity === "WARNING" ? "warning" : "normal") : "normal"}
                value={String(alerts.length)}
                rawTierLabel={t("severeWarn", {
                  crit: alerts.filter((a) => a.severity === "CRITICAL").length,
                  warn: alerts.filter((a) => a.severity === "WARNING").length,
                })}
              />
            </div>

            {/* Pipeline */}
            <div className="flex gap-1 mb-5 overflow-x-auto">
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

            {/* 2-col: 알림(dedup) | 군집 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Card title={t("ruleAlerts")} badge={t("alertCount", { n: alerts.length })} badgeColor="green" className="mb-3" children={<></>} />
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

function TaskRow({ task }: { task: Task }) {
  const dot = task.priority === 1 ? "bg-danger" : task.priority === 2 ? "bg-warning" : "bg-text3";
  return (
    <Link href="/tasks" className="flex items-center gap-3 border border-border rounded-xl px-4 py-2.5 bg-surface hover:border-primary transition">
      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${dot}`} />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-semibold truncate">{task.title}</div>
        {(task.ear_tag || task.overdue_days) && (
          <div className="text-[11px] text-text3">
            {task.ear_tag}{task.overdue_days ? ` · +${task.overdue_days}d` : ""}
          </div>
        )}
      </div>
      <ArrowRight size={14} className="text-text3 flex-shrink-0" />
    </Link>
  );
}

function KpiCard({ t, label, tier, value, rawTierLabel }: {
  t: ReturnType<typeof useTranslations>; label: string; tier: KpiTier; value: string; rawTierLabel?: string;
}) {
  const s = TIER_STYLE[tier];
  const tierLabel = rawTierLabel ?? t(
    tier === "normal" ? "tierGood" : tier === "warning" ? "tierWarning" : tier === "critical" ? "tierCritical" : "tierInsufficient",
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
  const cls = alert.severity === "CRITICAL" ? "bg-red-soft border-danger/40 text-danger"
    : alert.severity === "WARNING" ? "bg-amber-soft border-warning/40 text-warning"
    : "bg-green-soft border-success/30 text-success";
  return (
    <div className={`border rounded-xl px-4 py-3 mb-2 flex items-start gap-3 ${cls}`}>
      <Icon size={16} className="flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <div className="text-xs font-semibold">{alertTitle(alert)}</div>
        {alert.current_value != null && (
          <div className="text-[10px] mt-0.5 opacity-75">
            {t("currentTarget", { cur: alert.current_value.toFixed(1), tgt: alert.target_value?.toFixed(1) ?? "-" })}
          </div>
        )}
      </div>
    </div>
  );
}

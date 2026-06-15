"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowRight } from "lucide-react";
import { alertsApi } from "@/lib/api/endpoints/alerts";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import type { OverdueSow, OverdueType } from "@/types/api.types";

// 6 overdue types → i18n label key + recommended action route + action label key
const OVERDUE_META: Record<
  OverdueType,
  { labelKey: string; action: "mating" | "weaning"; actionKey: string }
> = {
  gilt_no_estrus:             { labelKey: "giltNoEstrus",             action: "mating",  actionKey: "actionMating" },
  gilt_overdue_mating:        { labelKey: "giltOverdueMating",        action: "mating",  actionKey: "actionMating" },
  pregnant_overdue_farrowing: { labelKey: "pregnantOverdueFarrowing", action: "mating",  actionKey: "actionPregnancyCheck" },
  lactating_overdue_weaning:  { labelKey: "lactatingOverdueWeaning",  action: "weaning", actionKey: "actionWeaning" },
  open_overdue_mating:        { labelKey: "openOverdueMating",        action: "mating",  actionKey: "actionMating" },
  accident_overdue_mating:    { labelKey: "accidentOverdueMating",    action: "mating",  actionKey: "actionMating" },
};

const CULL_REASON_KEYS: Record<string, string> = {
  repeat_rts: "reasonRepeatRts",
  aged_low_performer: "reasonAgedLowPerformer",
  overdue_gilt: "reasonOverdueGilt",
};

function actionHref(row: OverdueSow): string {
  const meta = OVERDUE_META[row.type];
  return `/record?tab=${meta.action}&sowId=${row.sow_id}`;
}

export default function AlertsPage() {
  const t = useTranslations("alerts");
  const tStatus = useTranslations("sowStatus");
  const farmId = useAuthStore((s) => s.activeFarmId);

  const { data: overdue, isLoading: loadingOverdue } = useQuery({
    queryKey: queryKeys.alerts.overdue(farmId ?? ""),
    queryFn: () => alertsApi.overdue(farmId!),
    enabled: !!farmId,
  });

  const { data: cullCandidates, isLoading: loadingCull } = useQuery({
    queryKey: queryKeys.alerts.cullCandidates(farmId ?? ""),
    queryFn: () => alertsApi.cullCandidates(farmId!),
    enabled: !!farmId,
  });

  if (!farmId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text3">{t("selectFarm")}</p>
      </div>
    );
  }

  const items = overdue?.items ?? [];
  const counts = overdue?.counts ?? {};
  const culls = cullCandidates ?? [];

  return (
    <div className="p-7 max-w-5xl">
      <div className="mb-6 flex items-center gap-2">
        <AlertTriangle className="w-5 h-5 text-warning" />
        <div>
          <h1 className="text-[22px] font-extrabold tracking-tight">{t("title")}</h1>
          <p className="text-xs text-text3 mt-0.5">{t("subtitle")}</p>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-7">
        {(Object.keys(OVERDUE_META) as OverdueType[]).map((type) => (
          <div key={type} className="border border-border rounded-2xl px-4 py-3 bg-surface">
            <div className="text-[11px] text-text3 leading-tight mb-1">{t(OVERDUE_META[type].labelKey)}</div>
            <div className="text-2xl font-extrabold font-mono tabular-nums">
              {counts[type] ?? 0}
            </div>
          </div>
        ))}
        <div className="border border-red-200 rounded-2xl px-4 py-3 bg-red-50 col-span-2 md:col-span-1">
          <div className="text-[11px] text-danger leading-tight mb-1">{t("cullRecommendations")}</div>
          <div className="text-2xl font-extrabold font-mono tabular-nums text-danger">
            {culls.length}
          </div>
        </div>
      </div>

      {/* Overdue table */}
      <section className="mb-8">
        <div className="text-[11px] font-bold text-faint uppercase tracking-widest mb-2">
          {t("overdueListTitle")} ({overdue?.total ?? 0})
        </div>
        {loadingOverdue ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 bg-border rounded-xl animate-pulse" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="border border-border rounded-2xl py-12 text-center text-text3">
            <p className="font-semibold">{t("emptyOverdueTitle")}</p>
            <p className="text-xs mt-1">{t("emptyOverdueDesc")}</p>
          </div>
        ) : (
          <div className="border border-border rounded-2xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-bg2 text-text3 text-[11px] uppercase tracking-wide">
                  <th className="text-left font-semibold px-4 py-2.5">{t("colType")}</th>
                  <th className="text-left font-semibold px-4 py-2.5">{t("colEarTag")}</th>
                  <th className="text-left font-semibold px-4 py-2.5">{t("colStatus")}</th>
                  <th className="text-right font-semibold px-4 py-2.5">{t("colOverdueDays")}</th>
                  <th className="text-right font-semibold px-4 py-2.5">{t("colAction")}</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr key={`${row.type}-${row.sow_id}`} className="border-t border-border">
                    <td className="px-4 py-2.5">{t(OVERDUE_META[row.type].labelKey)}</td>
                    <td className="px-4 py-2.5 font-mono font-semibold">{row.ear_tag}</td>
                    <td className="px-4 py-2.5 text-text3">{tStatus(row.status)}</td>
                    <td className="px-4 py-2.5 text-right font-mono tabular-nums text-warning font-semibold">
                      {t("overdueDays", { days: row.overdue_days })}
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      <Link
                        href={actionHref(row)}
                        className="inline-flex items-center gap-1 text-primary text-xs font-semibold hover:underline"
                      >
                        {t(OVERDUE_META[row.type].actionKey)}
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Cull recommendations */}
      <section>
        <div className="text-[11px] font-bold text-faint uppercase tracking-widest mb-2">
          {t("cullRecommendations")} ({culls.length})
        </div>
        {loadingCull ? (
          <div className="h-12 bg-border rounded-xl animate-pulse" />
        ) : culls.length === 0 ? (
          <div className="border border-border rounded-2xl py-10 text-center text-text3">
            <p className="text-sm">{t("emptyCull")}</p>
          </div>
        ) : (
          <div className="space-y-2">
            {culls.map((c) => (
              <div
                key={c.sow_id}
                className="border border-border rounded-2xl px-4 py-3 flex items-center justify-between gap-3"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono font-semibold text-sm">{c.ear_tag}</span>
                    <span className="text-[11px] text-text3">
                      {tStatus(c.status)} · {t("parity")} {c.parity}
                      {c.last_weaned != null && ` · ${t("lastWeaned", { n: c.last_weaned })}`}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {c.reasons.map((r) => (
                      <span
                        key={r}
                        className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-red-50 text-danger border border-red-200"
                      >
                        {CULL_REASON_KEYS[r] ? t(CULL_REASON_KEYS[r]) : r}
                      </span>
                    ))}
                  </div>
                </div>
                <Link
                  href={`/sows/${c.sow_id}`}
                  className="inline-flex items-center gap-1 text-text3 text-xs font-semibold hover:text-text shrink-0"
                >
                  {t("detail")}
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

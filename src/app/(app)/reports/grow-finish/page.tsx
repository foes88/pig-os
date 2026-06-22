"use client";

import { localToday } from "@/lib/date";
import { useState } from "react";
import { useTranslations } from "next-intl";
import { ReportsTabs } from "@/components/ReportsTabs";

import { downloadCsv } from "@/lib/utils/csv";
import { useQuery } from "@tanstack/react-query";
import { Download } from "lucide-react";
import { reportsApi } from "@/lib/api/endpoints/reports";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import type { GrowFinishRow } from "@/types/api.types";

function monthsAgoISO(n: number): string {
  const d = new Date();
  d.setMonth(d.getMonth() - n);
  return d.toISOString().slice(0, 10);
}
const TODAY = localToday();

const PRESETS = [
  { labelKey: "p6m", months: 6 },
  { labelKey: "p1y", months: 12 },
  { labelKey: "p2y", months: 24 },
];

function fmt(v: number | null, suffix = ""): string {
  return v == null ? "-" : `${v}${suffix}`;
}


export default function GrowFinishReportPage() {
  const t = useTranslations("growFinish");
  const farmId = useAuthStore((s) => s.activeFarmId);
  const [months, setMonths] = useState(12);
  const start = monthsAgoISO(months);

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.reports.growFinish(farmId ?? "", start, TODAY),
    queryFn: () => reportsApi.growFinish(farmId!, start, TODAY),
    enabled: !!farmId,
  });

  if (!farmId) return <div className="p-7 text-text3">{t("selectFarm")}</div>;

  const rows: GrowFinishRow[] = data ?? [];

  const exportCsv = () => {
    downloadCsv(
      `pigos_grow_finish_${start}_${TODAY}.csv`,
      [t("cGroup"), t("cEntryDate"), t("cEndDate"), t("cHeadIn"), t("cHeadOut"), t("cEntryWt"), t("cExitWt"), "ADG(g)", "FCR", t("cMortality")],
      rows.map((r) => [
        r.group_code, r.start_date, r.end_date, r.head_in, r.head_out,
        r.avg_entry_weight_kg, r.avg_exit_weight_kg, r.adg_g, r.fcr, r.mortality_rate,
      ]),
    );
  };

  return (
    <div className="p-7 max-w-5xl">
      <ReportsTabs />
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-[22px] font-extrabold tracking-tight">{t("title")}</h1>
          <p className="text-xs text-text3 mt-0.5">{t("subtitle")}</p>
        </div>
        <button
          onClick={exportCsv}
          disabled={rows.length === 0}
          className="inline-flex items-center gap-1.5 text-sm font-semibold border border-border rounded-xl px-3.5 py-2 hover:border-primary disabled:opacity-50"
        >
          <Download className="w-4 h-4" />
          CSV
        </button>
      </div>

      <div className="flex gap-2 mb-5">
        {PRESETS.map((p) => (
          <button
            key={p.months}
            onClick={() => setMonths(p.months)}
            className={`text-xs font-semibold rounded-full px-3.5 py-1.5 border transition ${
              months === p.months
                ? "bg-primary text-white border-primary"
                : "border-border text-text3 hover:border-primary"
            }`}
          >
            {t(p.labelKey)}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="h-40 bg-border rounded-2xl animate-pulse" />
      ) : rows.length === 0 ? (
        <div className="border border-border rounded-2xl py-16 text-center text-text3">
          {t("noData")}
        </div>
      ) : (
        <div className="border border-border rounded-2xl overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-bg2 text-text3 text-[11px] uppercase tracking-wide">
                <th className="text-left font-semibold px-3 py-2.5">{t("cGroup")}</th>
                <th className="text-right font-semibold px-3 py-2.5">{t("cHeadIn")}</th>
                <th className="text-right font-semibold px-3 py-2.5">{t("cHeadOut")}</th>
                <th className="text-right font-semibold px-3 py-2.5">ADG(g)</th>
                <th className="text-right font-semibold px-3 py-2.5">FCR</th>
                <th className="text-right font-semibold px-3 py-2.5">{t("cMortality")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.group_code} className="border-t border-border">
                  <td className="px-3 py-2.5 font-mono font-semibold">{r.group_code}</td>
                  <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.head_in}</td>
                  <td className="px-3 py-2.5 text-right font-mono tabular-nums">{fmt(r.head_out)}</td>
                  <td className="px-3 py-2.5 text-right font-mono tabular-nums">{fmt(r.adg_g)}</td>
                  <td className="px-3 py-2.5 text-right font-mono tabular-nums">{fmt(r.fcr)}</td>
                  <td className="px-3 py-2.5 text-right font-mono tabular-nums">{fmt(r.mortality_rate, "%")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

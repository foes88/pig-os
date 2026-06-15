"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { Download } from "lucide-react";
import { reportsApi } from "@/lib/api/endpoints/reports";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import type { ReproductionRow } from "@/types/api.types";

function monthsAgoISO(n: number): string {
  const d = new Date();
  d.setMonth(d.getMonth() - n);
  return d.toISOString().slice(0, 10);
}
const TODAY = new Date().toISOString().slice(0, 10);

const PRESETS = [
  { labelKey: "p3m", months: 3 },
  { labelKey: "p6m", months: 6 },
  { labelKey: "p1y", months: 12 },
];

const COLS: { key: keyof ReproductionRow; labelKey: string; pct?: boolean }[] = [
  { key: "total_matings", labelKey: "cMatings" },
  { key: "total_farrowings", labelKey: "cFarrowings" },
  { key: "total_weanings", labelKey: "cWeanings" },
  { key: "fr", labelKey: "cFr", pct: true },
  { key: "avg_tb", labelKey: "cAvgTb" },
  { key: "avg_ba", labelKey: "cAvgBa" },
  { key: "avg_weaned", labelKey: "cAvgWeaned" },
  { key: "avg_lactation_days", labelKey: "cLactDays" },
  { key: "pwmr_a", labelKey: "cPwmrA", pct: true },
  { key: "pwmr_b", labelKey: "cPwmrB", pct: true },
  { key: "rts_rate", labelKey: "cRts", pct: true },
];

function fmt(v: number | null, pct?: boolean): string {
  if (v == null) return "-";
  return pct ? `${v}%` : String(v);
}

function downloadCsv(filename: string, headers: string[], rows: (string | number | null)[][]) {
  const esc = (v: string | number | null) => (v == null ? "" : `${v}`);
  const csv = [headers.join(","), ...rows.map((r) => r.map(esc).join(","))].join("\n");
  const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ReproductionReportPage() {
  const t = useTranslations("reproReport");
  const farmId = useAuthStore((s) => s.activeFarmId);
  const [months, setMonths] = useState(6);
  const start = monthsAgoISO(months);

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.reports.reproduction(farmId ?? "", start, TODAY, "monthly"),
    queryFn: () => reportsApi.reproduction(farmId!, start, TODAY, "monthly"),
    enabled: !!farmId,
  });

  if (!farmId) return <div className="p-7 text-text3">{t("selectFarm")}</div>;

  const rows = data ?? [];

  const exportCsv = () => {
    downloadCsv(
      `pigos_reproduction_${start}_${TODAY}.csv`,
      [t("period"), ...COLS.map((c) => t(c.labelKey))],
      rows.map((r) => [r.period, ...COLS.map((c) => r[c.key] as number | null)]),
    );
  };

  return (
    <div className="p-7 max-w-5xl">
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
                <th className="text-left font-semibold px-3 py-2.5 sticky left-0 bg-bg2">{t("period")}</th>
                {COLS.map((c) => (
                  <th key={c.key} className="text-right font-semibold px-3 py-2.5">{t(c.labelKey)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.period} className="border-t border-border">
                  <td className="px-3 py-2.5 font-mono font-semibold sticky left-0 bg-surface">{r.period}</td>
                  {COLS.map((c) => (
                    <td key={c.key} className="px-3 py-2.5 text-right font-mono tabular-nums">
                      {fmt(r[c.key] as number | null, c.pct)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-[11px] text-text3 mt-3">
        {t("pwmrNote")}
      </p>
    </div>
  );
}

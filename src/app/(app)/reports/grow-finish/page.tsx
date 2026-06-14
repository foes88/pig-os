"use client";

import { useState } from "react";
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
const TODAY = new Date().toISOString().slice(0, 10);

const PRESETS = [
  { label: "최근 6개월", months: 6 },
  { label: "최근 1년", months: 12 },
  { label: "최근 2년", months: 24 },
];

function fmt(v: number | null, suffix = ""): string {
  return v == null ? "-" : `${v}${suffix}`;
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

export default function GrowFinishReportPage() {
  const farmId = useAuthStore((s) => s.activeFarmId);
  const [months, setMonths] = useState(12);
  const start = monthsAgoISO(months);

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.reports.growFinish(farmId ?? "", start, TODAY),
    queryFn: () => reportsApi.growFinish(farmId!, start, TODAY),
    enabled: !!farmId,
  });

  if (!farmId) return <div className="p-7 text-text3">농장을 선택해주세요.</div>;

  const rows: GrowFinishRow[] = data ?? [];

  const exportCsv = () => {
    downloadCsv(
      `pigos_grow_finish_${start}_${TODAY}.csv`,
      ["그룹", "입식일", "종료일", "입식두수", "출하두수", "입식체중", "출하체중", "ADG(g)", "FCR", "폐사율"],
      rows.map((r) => [
        r.group_code, r.start_date, r.end_date, r.head_in, r.head_out,
        r.avg_entry_weight_kg, r.avg_exit_weight_kg, r.adg_g, r.fcr, r.mortality_rate,
      ]),
    );
  };

  return (
    <div className="p-7 max-w-5xl">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-[22px] font-extrabold tracking-tight">비육 성적 보고서</h1>
          <p className="text-xs text-text3 mt-0.5">그룹별 ADG / FCR / 폐사율</p>
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
            {p.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="h-40 bg-border rounded-2xl animate-pulse" />
      ) : rows.length === 0 ? (
        <div className="border border-border rounded-2xl py-16 text-center text-text3">
          해당 기간 데이터가 없습니다.
        </div>
      ) : (
        <div className="border border-border rounded-2xl overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-bg2 text-text3 text-[11px] uppercase tracking-wide">
                <th className="text-left font-semibold px-3 py-2.5">그룹</th>
                <th className="text-right font-semibold px-3 py-2.5">입식두수</th>
                <th className="text-right font-semibold px-3 py-2.5">출하두수</th>
                <th className="text-right font-semibold px-3 py-2.5">ADG(g)</th>
                <th className="text-right font-semibold px-3 py-2.5">FCR</th>
                <th className="text-right font-semibold px-3 py-2.5">폐사율</th>
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

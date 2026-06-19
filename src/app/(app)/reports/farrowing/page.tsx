"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { Baby } from "lucide-react";

import { reportsApi } from "@/lib/api/endpoints/reports";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";

function isoDaysAgo(n: number): string {
  return new Date(Date.now() - n * 86_400_000).toISOString().slice(0, 10);
}
const today = () => new Date().toISOString().slice(0, 10);

const PRESETS = [
  { label: "3M", days: 90 },
  { label: "6M", days: 180 },
  { label: "1Y", days: 365 },
];

export default function FarrowingReportPage() {
  const t = useTranslations("farrowingReport");
  const farmId = useAuthStore((s) => s.activeFarmId);
  const [days, setDays] = useState(365);
  const start = isoDaysAgo(days);
  const end = today();

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.reports.farrowing(farmId ?? "", start, end),
    queryFn: () => reportsApi.farrowing(farmId!, start, end),
    enabled: !!farmId,
  });

  const rows = data ?? [];
  const num = (v: number | null) => (v == null ? "—" : v.toFixed(1));

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <header className="mb-4">
        <h1 className="text-xl font-extrabold text-text flex items-center gap-2">
          <Baby size={20} className="text-primary" /> {t("title")}
        </h1>
        <p className="text-sm text-text3 mt-1">{t("subtitle")}</p>
      </header>

      <div className="flex gap-2 mb-5">
        {PRESETS.map((p) => (
          <button
            key={p.label}
            onClick={() => setDays(p.days)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold font-mono border transition ${
              days === p.days ? "bg-navy text-white border-navy" : "bg-surface border-border text-text3"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <p className="text-sm text-text3 py-10 text-center">…</p>
      ) : rows.length === 0 ? (
        <div className="rounded-2xl border border-border bg-surface px-6 py-12 text-center text-sm text-text3">
          {t("noData")}
        </div>
      ) : (
        <div className="rounded-2xl border border-border overflow-x-auto">
          <table className="w-full text-sm whitespace-nowrap">
            <thead className="bg-surface text-text3 text-[11px] uppercase">
              <tr>
                <th className="text-left px-3 py-2.5 font-semibold">{t("parity")}</th>
                <th className="text-right px-3 py-2.5 font-semibold">{t("litters")}</th>
                <th className="text-right px-3 py-2.5 font-semibold">{t("tb")}</th>
                <th className="text-right px-3 py-2.5 font-semibold">{t("ba")}</th>
                <th className="text-right px-3 py-2.5 font-semibold">{t("sb")}</th>
                <th className="text-right px-3 py-2.5 font-semibold">{t("mum")}</th>
                <th className="text-right px-3 py-2.5 font-semibold">{t("weaned")}</th>
                <th className="text-right px-3 py-2.5 font-semibold">{t("lactDays")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border font-mono">
              {rows.map((r) => (
                <tr key={r.parity} className="hover:bg-bg2/40">
                  <td className="px-3 py-2.5 font-bold text-text1">{r.parity}</td>
                  <td className="px-3 py-2.5 text-right">{r.farrowings}</td>
                  <td className="px-3 py-2.5 text-right">{num(r.avg_total_born)}</td>
                  <td className="px-3 py-2.5 text-right text-success">{num(r.avg_born_alive)}</td>
                  <td className="px-3 py-2.5 text-right text-danger">{num(r.avg_stillborn)}</td>
                  <td className="px-3 py-2.5 text-right text-warning">{num(r.avg_mummified)}</td>
                  <td className="px-3 py-2.5 text-right font-bold">{num(r.avg_weaned)}</td>
                  <td className="px-3 py-2.5 text-right">{num(r.avg_lactation_days)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

"use client";

import { useTranslations } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { PiggyBank } from "lucide-react";

import { reportsApi } from "@/lib/api/endpoints/reports";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";

const STATUSES = ["GILT", "OPEN", "PREGNANT", "LACTATING", "ACCIDENT"] as const;
const STATUS_COLOR: Record<string, string> = {
  GILT: "text-purple", OPEN: "text-text2", PREGNANT: "text-primary",
  LACTATING: "text-success", ACCIDENT: "text-danger",
};

export default function SowStatusReportPage() {
  const t = useTranslations("sowStatusReport");
  const tStatus = useTranslations("sowStatus");
  const farmId = useAuthStore((s) => s.activeFarmId);

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.reports.sowStatus(farmId ?? ""),
    queryFn: () => reportsApi.sowStatus(farmId!),
    enabled: !!farmId,
  });

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <header className="mb-5">
        <h1 className="text-xl font-extrabold text-text flex items-center gap-2">
          <PiggyBank size={20} className="text-primary" /> {t("title")}
        </h1>
        <p className="text-sm text-text3 mt-1">{t("subtitle")}</p>
      </header>

      <div className="grid grid-cols-3 sm:grid-cols-6 gap-3 mb-6">
        <div className="rounded-2xl border border-border bg-surface px-3 py-3">
          <div className="text-[11px] text-text3 font-semibold">{t("total")}</div>
          <div className="text-2xl font-extrabold font-mono mt-0.5">{data?.total ?? "—"}</div>
        </div>
        {STATUSES.map((s) => (
          <div key={s} className="rounded-2xl border border-border bg-surface px-3 py-3">
            <div className={`text-[11px] font-semibold ${STATUS_COLOR[s]}`}>{tStatus(s)}</div>
            <div className="text-2xl font-extrabold font-mono mt-0.5">{data?.by_status?.[s] ?? 0}</div>
          </div>
        ))}
      </div>

      {isLoading ? (
        <p className="text-sm text-text3 py-10 text-center">…</p>
      ) : !data || data.sows.length === 0 ? (
        <div className="rounded-2xl border border-border bg-surface px-6 py-12 text-center text-sm text-text3">
          {t("empty")}
        </div>
      ) : (
        <div className="rounded-2xl border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-surface text-text3 text-[11px] uppercase">
              <tr>
                <th className="text-left px-4 py-2.5 font-semibold">{t("colTag")}</th>
                <th className="text-left px-4 py-2.5 font-semibold">{t("colStatus")}</th>
                <th className="text-right px-4 py-2.5 font-semibold">{t("colParity")}</th>
                <th className="text-left px-4 py-2.5 font-semibold">{t("colEntry")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {data.sows.map((s) => (
                <tr key={s.sow_id} className="hover:bg-bg2/40">
                  <td className="px-4 py-2.5 font-mono font-bold text-text1">{s.ear_tag}</td>
                  <td className={`px-4 py-2.5 font-semibold ${STATUS_COLOR[s.status] ?? "text-text2"}`}>
                    {tStatus(s.status)}
                  </td>
                  <td className="px-4 py-2.5 text-right font-mono">{s.parity}</td>
                  <td className="px-4 py-2.5 text-text3 font-mono text-xs">{s.entry_date ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

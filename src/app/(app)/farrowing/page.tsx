"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { eventsApi } from "@/lib/api/endpoints/events";
import { sowsApi } from "@/lib/api/endpoints/sows";
import { kpiApi } from "@/lib/api/endpoints/kpi";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import type { Farrowing } from "@/types/api.types";

export default function FarrowingPage() {
  const t = useTranslations("farrowing");
  const farmId = useAuthStore((s) => s.activeFarmId);

  const { data: kpi } = useQuery({
    queryKey: queryKeys.kpi.dashboard(farmId ?? ""),
    queryFn: () => kpiApi.dashboard(farmId!),
    enabled: !!farmId,
  });

  const { data: farrowings = [], isLoading } = useQuery({
    queryKey: ["farrowings", farmId],
    queryFn: () => eventsApi.farrowings.list(farmId!),
    enabled: !!farmId,
  });

  const { data: sowData } = useQuery({
    queryKey: queryKeys.sows.list(farmId ?? "", { status: "LACTATING" }),
    queryFn: () => sowsApi.list(farmId!, { status: "LACTATING", per_page: 200 }),
    enabled: !!farmId,
  });

  if (!farmId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text3">{t("selectFarm")}</p>
      </div>
    );
  }

  const lactating = sowData?.items ?? [];
  const recent = [...farrowings]
    .sort((a, b) => b.farrowing_date.localeCompare(a.farrowing_date))
    .slice(0, 30);

  const avgBornAlive =
    farrowings.length > 0
      ? (farrowings.reduce((s, f) => s + f.born_alive, 0) / farrowings.length).toFixed(1)
      : "-";
  const avgStillborn =
    farrowings.length > 0
      ? (farrowings.reduce((s, f) => s + f.stillborn, 0) / farrowings.length).toFixed(1)
      : "-";

  return (
    <div className="p-7">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-[22px] font-extrabold tracking-tight">{t("title")}</h1>
          <p className="text-xs text-text3 mt-0.5">
            {t("subtitle", {
              n: kpi?.lactating ?? 0,
              fr: kpi?.farrowing_rate != null ? `${kpi.farrowing_rate.toFixed(1)}%` : "-",
            })}
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {[
          { label: t("statLactating"), value: String(kpi?.lactating ?? 0), unit: t("headUnit"), color: "text-success" },
          { label: t("statFarrowingRate"), value: kpi?.farrowing_rate != null ? kpi.farrowing_rate.toFixed(1) : "-", unit: "%", color: "text-primary" },
          { label: t("statAvgBornAlive"), value: avgBornAlive, unit: t("headUnit"), color: "text-text" },
          { label: t("statAvgStillborn"), value: avgStillborn, unit: t("headUnit"), color: "text-danger" },
        ].map(({ label, value, unit, color }) => (
          <div key={label} className="bg-surface border border-border rounded-2xl p-4">
            <div className="text-xs text-text3 mb-1">{label}</div>
            <div className={`text-2xl font-extrabold font-mono tracking-tight ${color}`}>
              {value}<span className="text-sm font-normal text-text3 ml-1">{unit}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid md:grid-cols-2 gap-5">
        {/* 포유 중 모돈 */}
        <div>
          <h2 className="text-sm font-bold text-text mb-3">{t("lactatingTitle", { n: lactating.length })}</h2>
          {lactating.length === 0 ? (
            <div className="bg-surface border border-border rounded-2xl p-8 text-center text-sm text-text3">
              {t("lactatingEmpty")}
            </div>
          ) : (
            <div className="bg-surface border border-border rounded-2xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left px-4 py-2.5 text-xs font-semibold text-text3">{t("thEarTag")}</th>
                    <th className="text-center px-4 py-2.5 text-xs font-semibold text-text3">{t("thParity")}</th>
                  </tr>
                </thead>
                <tbody>
                  {lactating.slice(0, 15).map((sow, i) => (
                    <tr key={sow.id} className={i < lactating.length - 1 ? "border-b border-border" : ""}>
                      <td className="px-4 py-2.5 font-mono font-semibold text-text">{sow.ear_tag}</td>
                      <td className="px-4 py-2.5 text-center text-text3">{t("parityUnit", { n: sow.parity })}</td>
                    </tr>
                  ))}
                  {lactating.length > 15 && (
                    <tr>
                      <td colSpan={2} className="px-4 py-2 text-xs text-text3 text-center">
                        {t("more", { n: lactating.length - 15 })}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* 최근 분만 기록 */}
        <div>
          <h2 className="text-sm font-bold text-text mb-3">{t("recentTitle")}</h2>
          {isLoading ? (
            <div className="bg-surface border border-border rounded-2xl p-8 text-center text-sm text-text3">
              {t("loading")}
            </div>
          ) : recent.length === 0 ? (
            <div className="bg-surface border border-border rounded-2xl p-8 text-center text-sm text-text3">
              {t("recentEmpty")}
            </div>
          ) : (
            <div className="bg-surface border border-border rounded-2xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left px-4 py-2.5 text-xs font-semibold text-text3">{t("thDate")}</th>
                    <th className="text-center px-4 py-2.5 text-xs font-semibold text-text3">{t("thBornAlive")}</th>
                    <th className="text-center px-4 py-2.5 text-xs font-semibold text-text3">{t("thStillborn")}</th>
                    <th className="text-center px-4 py-2.5 text-xs font-semibold text-text3">{t("thTotalBorn")}</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.map((f: Farrowing, i) => (
                    <tr key={f.id} className={i < recent.length - 1 ? "border-b border-border" : ""}>
                      <td className="px-4 py-2.5 font-mono text-xs text-text2">{f.farrowing_date}</td>
                      <td className="px-4 py-2.5 text-center font-bold text-success">{f.born_alive}</td>
                      <td className="px-4 py-2.5 text-center text-danger">{f.stillborn}</td>
                      <td className="px-4 py-2.5 text-center text-text3">{f.total_born}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

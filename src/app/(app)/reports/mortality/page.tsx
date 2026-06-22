"use client";

import { localToday } from "@/lib/date";
import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { TrendingDown } from "lucide-react";

import { reportsApi } from "@/lib/api/endpoints/reports";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import type { MortalityCount } from "@/types/api.types";

function isoDaysAgo(n: number): string {
  return new Date(Date.now() - n * 86_400_000).toISOString().slice(0, 10);
}
const today = () => localToday();
const titleCase = (k: string) => k.charAt(0) + k.slice(1).toLowerCase();
const PRESETS = [
  { label: "3M", days: 90 },
  { label: "6M", days: 180 },
  { label: "1Y", days: 365 },
];

export default function MortalityReportPage() {
  const t = useTranslations("mortalityReport");
  const tr = useTranslations("record");
  const farmId = useAuthStore((s) => s.activeFarmId);
  const [days, setDays] = useState(365);
  const start = isoDaysAgo(days);
  const end = today();

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.reports.mortality(farmId ?? "", start, end),
    queryFn: () => reportsApi.mortality(farmId!, start, end),
    enabled: !!farmId,
  });

  // 백엔드 키(CULLED/REPRODUCTIVE/CRUSHING) → record 네임스페이스 라벨
  const label = (prefix: string, key: string) => {
    const k = `${prefix}${titleCase(key)}`;
    return tr.has(k) ? tr(k) : key;
  };

  const List = ({ title, items, prefix, showPiglets }: {
    title: string; items: MortalityCount[]; prefix: string; showPiglets?: boolean;
  }) => (
    <div className="rounded-2xl border border-border bg-bg2/30 p-4">
      <div className="text-sm font-bold text-text mb-3">{title}</div>
      {items.length === 0 ? (
        <p className="text-xs text-text3">{t("noData")}</p>
      ) : (
        <ul className="space-y-1.5">
          {items.map((i) => (
            <li key={i.key} className="flex items-center justify-between text-sm">
              <span className="text-text2">{label(prefix, i.key)}</span>
              <span className="font-mono font-bold">
                {showPiglets ? `${i.piglets ?? 0}` : i.count}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <header className="mb-4">
        <h1 className="text-xl font-extrabold text-text flex items-center gap-2">
          <TrendingDown size={20} className="text-danger" /> {t("title")}
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
      ) : (
        <>
          <div className="grid grid-cols-3 gap-3 mb-6">
            <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3">
              <div className="text-[11px] text-danger font-bold">{t("preWeanRate")}</div>
              <div className="text-3xl font-extrabold font-mono text-danger mt-1">
                {data?.preweaning_mortality_rate != null ? `${data.preweaning_mortality_rate}%` : "—"}
              </div>
            </div>
            <div className="rounded-2xl border border-border bg-surface px-4 py-3">
              <div className="text-[11px] text-text3 font-bold">{t("removals")}</div>
              <div className="text-3xl font-extrabold font-mono mt-1">{data?.total_removals ?? 0}</div>
            </div>
            <div className="rounded-2xl border border-border bg-surface px-4 py-3">
              <div className="text-[11px] text-text3 font-bold">{t("pigletDeaths")}</div>
              <div className="text-3xl font-extrabold font-mono mt-1">{data?.total_piglet_deaths ?? 0}</div>
            </div>
          </div>

          <div className="grid sm:grid-cols-3 gap-3">
            <List title={t("byType")} items={data?.removals_by_type ?? []} prefix="rm" />
            <List title={t("byReason")} items={data?.removals_by_reason ?? []} prefix="rc" />
            <List title={t("pigletByReason")} items={data?.piglet_deaths_by_reason ?? []} prefix="pc" showPiglets />
          </div>
        </>
      )}
    </div>
  );
}

"use client";

import { localToday } from "@/lib/date";
import { useState } from "react";
import { useTranslations } from "next-intl";
import { ReportsTabs } from "@/components/ReportsTabs";
import { useQuery } from "@tanstack/react-query";
import { FileText } from "lucide-react";

import { reportsApi } from "@/lib/api/endpoints/reports";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import type { ComprehensiveDailyReport } from "@/types/api.types";

const today = () => localToday();

export default function ComprehensiveDailyPage() {
  const t = useTranslations("comprehensiveDaily");
  const farmId = useAuthStore((s) => s.activeFarmId);
  const [date, setDate] = useState(today());

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.reports.comprehensiveDaily(farmId ?? "", date),
    queryFn: () => reportsApi.comprehensiveDaily(farmId!, date),
    enabled: !!farmId,
  });

  return (
    <div className="max-w-[1600px] mx-auto px-4 py-6">
      <ReportsTabs />
      <header className="flex items-center justify-between mb-5 flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-extrabold text-text flex items-center gap-2">
            <FileText size={20} className="text-primary" /> {t("title")}
          </h1>
          <p className="text-sm text-text3 mt-1">{t("subtitle")}</p>
        </div>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
          className="px-3 py-2 rounded-lg border border-border bg-surface text-sm font-mono outline-none focus:border-primary" />
      </header>

      {isLoading || !data ? (
        <p className="text-sm text-text3 py-10 text-center">…</p>
      ) : (
        <div className="space-y-5">
          {/* ① 돈군 현황 */}
          <Section title={t("herd")}>
            <div className="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-9 gap-2">
              <Stat label={t("gilt")} v={data.herd.gilt} />
              <Stat label={t("open")} v={data.herd.open} />
              <Stat label={t("pregnant")} v={data.herd.pregnant} />
              <Stat label={t("lactating")} v={data.herd.lactating} />
              <Stat label={t("accident")} v={data.herd.accident} />
              <Stat label={t("sowsTotal")} v={data.herd.sows_total} accent />
              <Stat label={t("boars")} v={data.herd.boars} />
              <Stat label={t("nursingPiglets")} v={data.herd.nursing_piglets} />
              <Stat label={t("finishers")} v={data.herd.finishers} />
            </div>
          </Section>

          {/* ③ 교배 / ④ 임신사고 */}
          <div className="grid md:grid-cols-2 gap-5">
            <Section title={t("mating")}>
              <DM t={t} rows={[
                ["matTotal", data.mating.day.total, data.mating.month.total],
                ["matGilt", data.mating.day.gilt, data.mating.month.gilt],
                ["matSow", data.mating.day.sow, data.mating.month.sow],
                ["matRebreed", data.mating.day.rebreed, data.mating.month.rebreed],
              ]} />
            </Section>
            <Section title={t("accidents")}>
              <DM t={t} rows={[
                ["accTotal", data.accidents.day.total, data.accidents.month.total],
                ["accRts", data.accidents.day.rts, data.accidents.month.rts],
                ["accAbortion", data.accidents.day.abortion, data.accidents.month.abortion],
                ["accEmpty", data.accidents.day.empty, data.accidents.month.empty],
                ["accInfertile", data.accidents.day.infertile, data.accidents.month.infertile],
              ]} />
            </Section>
          </div>

          {/* ⑤ 생산현황 */}
          <Section title={t("production")}>
            <DM t={t} rows={[
              ["prodFarrowings", data.production.day.farrowings, data.production.month.farrowings],
              ["prodTotalBorn", data.production.day.total_born, data.production.month.total_born],
              ["prodBornAlive", data.production.day.born_alive, data.production.month.born_alive],
              ["prodStillborn", data.production.day.stillborn, data.production.month.stillborn],
              ["prodMummified", data.production.day.mummified, data.production.month.mummified],
              ["prodAvgBw", data.production.day.avg_birth_weight, data.production.month.avg_birth_weight],
              ["prodWeanings", data.production.day.weanings, data.production.month.weanings],
              ["prodWeaned", data.production.day.weaned, data.production.month.weaned],
              ["prodAvgWw", data.production.day.avg_weaning_weight, data.production.month.avg_weaning_weight],
              ["prodAvgWa", data.production.day.avg_weaning_age, data.production.month.avg_weaning_age],
              ["prodPigletDeaths", data.production.day.piglet_deaths, data.production.month.piglet_deaths],
            ]} />
          </Section>

          {/* ⑥ 전입출·폐사 */}
          <Section title={t("inout")}>
            <DM t={t} rows={[
              ["ioGiltIn", data.inout.day.gilt_in, data.inout.month.gilt_in],
              ["ioSowIn", data.inout.day.sow_in, data.inout.month.sow_in],
              ["ioDead", data.inout.day.dead, data.inout.month.dead],
              ["ioCulled", data.inout.day.culled, data.inout.month.culled],
              ["ioSold", data.inout.day.sold, data.inout.month.sold],
              ["ioTransfer", data.inout.day.transfer, data.inout.month.transfer],
              ["ioBoarIn", data.inout.day.boar_in, data.inout.month.boar_in],
            ]} />
          </Section>
        </div>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-4" style={{ boxShadow: "var(--shadow-card)" }}>
      <div className="text-sm font-bold text-text mb-3">{title}</div>
      {children}
    </div>
  );
}

function Stat({ label, v, accent }: { label: string; v: number; accent?: boolean }) {
  return (
    <div className={`rounded-lg border px-2.5 py-2 ${accent ? "border-success/30 bg-green-soft" : "border-border bg-bg2/40"}`}>
      <div className="text-[10px] text-muted truncate">{label}</div>
      <div className={`text-lg font-extrabold font-mono ${accent ? "text-success" : "text-text"}`}>{v}</div>
    </div>
  );
}

// 일계/월계 2열 테이블
function DM({ t, rows }: { t: (k: string) => string; rows: [string, number | null, number | null][] }) {
  const fmt = (v: number | null) => (v == null ? "—" : v);
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-[11px] text-text3 uppercase">
          <th className="text-left font-semibold pb-1.5" />
          <th className="text-right font-semibold pb-1.5 px-2">{t("day")}</th>
          <th className="text-right font-semibold pb-1.5 px-2">{t("month")}</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-border">
        {rows.map(([k, d, m]) => (
          <tr key={k}>
            <td className="py-1.5 text-text2">{t(k)}</td>
            <td className="py-1.5 px-2 text-right font-mono font-semibold">{fmt(d)}</td>
            <td className="py-1.5 px-2 text-right font-mono text-muted">{fmt(m)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

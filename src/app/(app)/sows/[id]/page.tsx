"use client";

import type { ReactNode } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Baby, Sprout, Syringe } from "lucide-react";
import { sowsApi } from "@/lib/api/endpoints/sows";
import { eventsApi } from "@/lib/api/endpoints/events";
import { farmsApi } from "@/lib/api/endpoints/farms";
import { RecentEventsSection } from "@/components/RecentEventsSection";
import { useAuthStore } from "@/store/auth.store";
import { canManage } from "@/lib/auth/permissions";

// 상태 배지 색상 (라벨은 sowStatus 키)
const STATUS_CLS: Record<string, string> = {
  GILT:      "bg-cyan-50 text-cyan-600",
  OPEN:      "bg-slate-100 text-slate-600",
  PREGNANT:  "bg-green-soft text-success",
  LACTATING: "bg-green-50 text-green-600",
  ACCIDENT:  "bg-orange-50 text-orange-600",
  CULLED:    "bg-red-50 text-red-500",
  DEAD:      "bg-gray-100 text-gray-500",
  SOLD:      "bg-emerald-50 text-emerald-600",
  TRANSFER:  "bg-amber-50 text-amber-600",
};

export default function SowDetailPage() {
  const t = useTranslations("sowDetail");
  const tStatus = useTranslations("sowStatus");
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const farmId = useAuthStore((s) => s.activeFarmId);
  const canManageRole = canManage(useAuthStore((s) => s.user?.role));

  const { data: sow, isLoading: sowLoading } = useQuery({
    queryKey: ["sow", farmId, id],
    queryFn: () => sowsApi.get(farmId!, id),
    enabled: !!farmId && !!id,
  });

  const { data: matings = [] } = useQuery({
    queryKey: ["matings", farmId, id],
    queryFn: () => eventsApi.matings.list(farmId!, id),
    enabled: !!farmId && !!id,
  });

  const { data: farrowings = [] } = useQuery({
    queryKey: ["farrowings", farmId, id],
    queryFn: () => eventsApi.farrowings.list(farmId!, id),
    enabled: !!farmId && !!id,
  });

  const { data: weanings = [] } = useQuery({
    queryKey: ["weanings", farmId, id],
    queryFn: () => eventsApi.weanings.list(farmId!, id),
    enabled: !!farmId && !!id,
  });

  const { data: reproConfig } = useQuery({
    queryKey: ["farms", farmId, "repro-config"],
    queryFn: () => farmsApi.getReproConfig(farmId!),
    enabled: !!farmId,
  });

  const qc = useQueryClient();
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["matings", farmId, id] });
    qc.invalidateQueries({ queryKey: ["farrowings", farmId, id] });
    qc.invalidateQueries({ queryKey: ["weanings", farmId, id] });
    qc.invalidateQueries({ queryKey: ["sow", farmId, id] });
  };
  const delMating = useMutation({ mutationFn: (eid: string) => eventsApi.matings.remove(farmId!, eid), onSuccess: invalidate });
  const delFarrowing = useMutation({ mutationFn: (eid: string) => eventsApi.farrowings.remove(farmId!, eid), onSuccess: invalidate });
  const delWeaning = useMutation({ mutationFn: (eid: string) => eventsApi.weanings.remove(farmId!, eid), onSuccess: invalidate });

  const deleteLatest = (cycle: { mating: { id: string }; farrowing?: { id: string }; weaning?: { id: string } }) => {
    if (cycle.weaning) {
      if (confirm(t("confirmDelWean"))) delWeaning.mutate(cycle.weaning.id);
    } else if (cycle.farrowing) {
      if (confirm(t("confirmDelFarrow"))) delFarrowing.mutate(cycle.farrowing.id);
    } else {
      if (confirm(t("confirmDelMating"))) delMating.mutate(cycle.mating.id);
    }
  };

  if (!farmId) return null;

  if (sowLoading) {
    return (
      <div className="p-7 text-center py-20 text-text3 text-sm">{t("loading")}</div>
    );
  }

  if (!sow) {
    return (
      <div className="p-7 text-center py-20 text-danger text-sm">{t("notFound")}</div>
    );
  }

  const badgeCls = STATUS_CLS[sow.status] ?? "bg-gray-100 text-gray-500";

  // 번식 이력 타임라인 합산 (교배 기준으로 산차별 묶기)
  const timeline = matings
    .map((m) => {
      const farrowing = farrowings.find((f) => f.mating_id === m.id);
      const weaning = farrowing ? weanings.find((w) => w.farrowing_id === farrowing.id) : undefined;
      return { mating: m, farrowing, weaning };
    })
    .sort((a, b) => b.mating.mating_date.localeCompare(a.mating.mating_date));

  const lastMating = [...matings].map((m) => m.mating_date).sort().at(-1);
  const lastFarrowing = [...farrowings].map((f) => f.farrowing_date).sort().at(-1);
  const lastWeaning = [...weanings].map((w) => w.weaning_date).sort().at(-1);
  const nextEvent = computeNextEvent(
    sow.status, lastMating, lastFarrowing, lastWeaning, reproConfig,
  );

  return (
    <div className="p-7 max-w-3xl">
        {/* 뒤로가기 */}
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1.5 text-xs text-text3 hover:text-text1 mb-5 transition"
        >
          ← {t("back")}
        </button>

        {/* 개체 헤더 */}
        <div className="bg-surface border border-border rounded-2xl p-6 mb-5">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h1 className="text-2xl font-extrabold font-mono tracking-tight">{sow.ear_tag}</h1>
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${badgeCls}`}>
                  {tStatus(sow.status)}
                </span>
              </div>
              {sow.rfid_tag && (
                <p className="text-xs text-text3 font-mono">RFID: {sow.rfid_tag}</p>
              )}
            </div>
            <div className="text-right">
              <div className="text-3xl font-extrabold font-mono text-primary">{t("parityUnit", { n: sow.parity })}</div>
              <div className="text-xs text-text3 mt-0.5">{t("parityLabel")}</div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 mt-5 pt-5 border-t border-border">
            <InfoCell label={t("breed")} value={sow.breed ?? "-"} />
            <InfoCell label={t("entryType")} value={sow.entry_type} />
            <InfoCell label={t("entryDate")} value={sow.entry_date.slice(0, 10)} mono />
          </div>
        </div>

        {/* 다음 예정 이벤트 (farm_config 기준) */}
        {nextEvent && (
          <div className="bg-primary/5 border border-primary/20 rounded-2xl px-5 py-4 mb-5 flex items-center justify-between">
            <div>
              <div className="text-[11px] text-primary font-bold uppercase tracking-wide">{t("nextEvent")}</div>
              <div className="text-sm font-semibold text-text mt-0.5">{t(nextEvent.labelKey)}</div>
            </div>
            <div className="text-right font-mono text-sm font-bold text-primary">
              {nextEvent.date ?? "—"}
            </div>
          </div>
        )}

        {/* 산차별 성적 */}
        {timeline.some((c) => c.farrowing) && (
          <div className="mb-5">
            <h2 className="text-sm font-bold mb-3 text-text2">{t("parityTable")}</h2>
            <div className="border border-border rounded-xl overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-bg2 text-text3 text-[11px] uppercase tracking-wide">
                    <th className="text-left font-semibold px-3 py-2">{t("thCycle")}</th>
                    <th className="text-left font-semibold px-3 py-2">{t("thMating")}</th>
                    <th className="text-left font-semibold px-3 py-2">{t("thFarrowing")}</th>
                    <th className="text-right font-semibold px-3 py-2">{t("thTotalBorn")}</th>
                    <th className="text-right font-semibold px-3 py-2">{t("thBornAlive")}</th>
                    <th className="text-right font-semibold px-3 py-2">{t("thWeaned")}</th>
                    <th className="text-right font-semibold px-3 py-2">{t("thWeanAge")}</th>
                  </tr>
                </thead>
                <tbody>
                  {timeline.map(({ mating, farrowing, weaning }, i) => (
                    <tr key={mating.id} className="border-t border-border">
                      <td className="px-3 py-2 font-mono">{timeline.length - i}</td>
                      <td className="px-3 py-2 font-mono text-text3">{mating.mating_date.slice(0, 10)}</td>
                      <td className="px-3 py-2 font-mono text-text3">{farrowing?.farrowing_date.slice(0, 10) ?? "-"}</td>
                      <td className="px-3 py-2 text-right font-mono">{farrowing?.total_born ?? "-"}</td>
                      <td className="px-3 py-2 text-right font-mono">{farrowing?.born_alive ?? "-"}</td>
                      <td className="px-3 py-2 text-right font-mono">{weaning?.weaned_count ?? "-"}</td>
                      <td className="px-3 py-2 text-right font-mono">{weaning?.weaning_age_days ?? "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 번식 이력 타임라인 */}
        <div>
          <h2 className="text-sm font-bold mb-3 text-text2">{t("timeline")}</h2>

          {timeline.length === 0 ? (
            <div className="bg-surface border border-border rounded-xl p-8 text-center text-text3 text-sm">
              {t("noTimeline")}
            </div>
          ) : (
            <div className="space-y-3">
              {timeline.map(({ mating, farrowing, weaning }, i) => (
                <div key={mating.id} className="bg-surface border border-border rounded-xl p-5">
                  {/* 사이클 헤더 */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-primary/10 text-primary text-[11px] font-bold flex items-center justify-center">
                        {timeline.length - i}
                      </span>
                      <span className="text-xs font-semibold text-text2">
                        {t("cycleHeader", { month: mating.mating_date.slice(0, 7) })}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        weaning ? "bg-green-50 text-green-600" :
                        farrowing ? "bg-amber-50 text-amber-600" :
                        "bg-green-soft text-success"
                      }`}>
                        {weaning ? t("cycleWeaned") : farrowing ? t("cycleNursing") : t("cyclePregnant")}
                      </span>
                      {canManageRole && (
                        <button
                          onClick={() => deleteLatest({ mating, farrowing, weaning })}
                          className="text-[10px] font-semibold text-danger border border-red-200 rounded-md px-2 py-0.5 hover:bg-red-50"
                        >
                          {t("deleteLatest")}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* 이벤트 스텝 */}
                  <div className="flex items-start gap-0">
                    {/* 교배 */}
                    <Step
                      icon={<Syringe size={16} />}
                      label={t("stepMating")}
                      date={mating.mating_date}
                      detail={mating.mating_type === "AI" ? t("mAI") : t("mNatural")}
                      done
                    />
                    <StepConnector done={!!farrowing} />

                    {/* 분만 */}
                    <Step
                      icon={<Baby size={16} />}
                      label={t("stepFarrowing")}
                      date={farrowing?.farrowing_date}
                      detail={farrowing ? t("farrowDetail", { a: farrowing.born_alive, s: farrowing.stillborn }) : undefined}
                      done={!!farrowing}
                    />
                    <StepConnector done={!!weaning} />

                    {/* 이유 */}
                    <Step
                      icon={<Sprout size={16} />}
                      label={t("stepWeaning")}
                      date={weaning?.weaning_date}
                      detail={weaning ? t("weanDetail", { n: weaning.weaned_count }) : undefined}
                      done={!!weaning}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 개별 이벤트 수정/삭제 (교배/분만/이유) */}
        <RecentEventsSection farmId={farmId} sowId={id} limit={10} onChanged={invalidate} />
    </div>
  );
}

function computeNextEvent(
  status: string,
  lastMating: string | undefined,
  lastFarrowing: string | undefined,
  lastWeaning: string | undefined,
  cfg: { gestation_days: number; lactation_days: number; wei_target_days: number } | undefined,
): { labelKey: string; date: string | null } | null {
  if (status === "GILT") return { labelKey: "neFirstMating", date: null };
  if (!cfg) return null;
  const addDays = (iso: string, d: number): string => {
    const x = new Date(iso);
    x.setDate(x.getDate() + d);
    return x.toISOString().slice(0, 10);
  };
  if (status === "PREGNANT" && lastMating)
    return { labelKey: "neFarrowingDue", date: addDays(lastMating, cfg.gestation_days) };
  if (status === "LACTATING" && lastFarrowing)
    return { labelKey: "neWeaningDue", date: addDays(lastFarrowing, cfg.lactation_days) };
  if (status === "OPEN" && lastWeaning)
    return { labelKey: "neRemateDue", date: addDays(lastWeaning, cfg.wei_target_days) };
  if (status === "ACCIDENT") return { labelKey: "neRemateNeeded", date: null };
  return null;
}

function InfoCell({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <div className="text-[10px] text-text3 mb-0.5">{label}</div>
      <div className={`text-sm font-medium text-text1 ${mono ? "font-mono" : ""}`}>{value}</div>
    </div>
  );
}

function Step({
  icon, label, date, detail, done,
}: {
  icon: ReactNode;
  label: string;
  date?: string;
  detail?: string;
  done: boolean;
}) {
  return (
    <div className="flex flex-col items-center flex-1 min-w-0">
      <div className={`w-9 h-9 rounded-full flex items-center justify-center text-base mb-1.5 ${
        done ? "bg-primary/10" : "bg-gray-100"
      }`}>
        {done ? icon : <span className="text-text3 text-sm">○</span>}
      </div>
      <div className="text-[11px] font-semibold text-text2">{label}</div>
      {date && <div className="text-[10px] text-text3 font-mono mt-0.5">{date}</div>}
      {detail && <div className="text-[10px] text-text3 mt-0.5 text-center leading-tight">{detail}</div>}
    </div>
  );
}

function StepConnector({ done }: { done: boolean }) {
  return (
    <div className="flex-shrink-0 w-8 flex items-center justify-center pt-4">
      <div className={`h-0.5 w-full ${done ? "bg-primary" : "bg-gray-200"}`} />
    </div>
  );
}

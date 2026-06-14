"use client";

import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { sowsApi } from "@/lib/api/endpoints/sows";
import { eventsApi } from "@/lib/api/endpoints/events";
import { farmsApi } from "@/lib/api/endpoints/farms";
import { useAuthStore } from "@/store/auth.store";

const STATUS_BADGE: Record<string, { label: string; cls: string }> = {
  GILT:      { label: "후보돈", cls: "bg-cyan-50 text-cyan-600" },
  OPEN:      { label: "공태",   cls: "bg-slate-100 text-slate-600" },
  PREGNANT:  { label: "임신",   cls: "bg-blue-50 text-blue-600" },
  LACTATING: { label: "포유",   cls: "bg-green-50 text-green-600" },
  ACCIDENT:  { label: "사고",   cls: "bg-orange-50 text-orange-600" },
  CULLED:    { label: "도태",   cls: "bg-red-50 text-red-500" },
  DEAD:      { label: "폐사",   cls: "bg-gray-100 text-gray-500" },
  SOLD:      { label: "판매",   cls: "bg-emerald-50 text-emerald-600" },
  TRANSFER:  { label: "전출",   cls: "bg-amber-50 text-amber-600" },
};

export default function SowDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const farmId = useAuthStore((s) => s.activeFarmId);

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
      if (confirm("이유 기록을 삭제하면 모돈 상태가 포유로 롤백됩니다. 계속할까요?")) delWeaning.mutate(cycle.weaning.id);
    } else if (cycle.farrowing) {
      if (confirm("분만 기록을 삭제하면 모돈 상태가 임신으로 롤백되고 산차가 1 감소합니다. 계속할까요?")) delFarrowing.mutate(cycle.farrowing.id);
    } else {
      if (confirm("교배 기록을 삭제하면 모돈 상태가 공태로 롤백됩니다. 계속할까요?")) delMating.mutate(cycle.mating.id);
    }
  };

  if (!farmId) return null;

  if (sowLoading) {
    return (
      <div className="p-7 text-center py-20 text-text3 text-sm">불러오는 중...</div>
    );
  }

  if (!sow) {
    return (
      <div className="p-7 text-center py-20 text-danger text-sm">모돈을 찾을 수 없습니다.</div>
    );
  }

  const badge = STATUS_BADGE[sow.status] ?? { label: sow.status, cls: "bg-gray-100 text-gray-500" };

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
          ← 모돈 목록
        </button>

        {/* 개체 헤더 */}
        <div className="bg-surface border border-border rounded-2xl p-6 mb-5">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h1 className="text-2xl font-extrabold font-mono tracking-tight">{sow.ear_tag}</h1>
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${badge.cls}`}>
                  {badge.label}
                </span>
              </div>
              {sow.rfid_tag && (
                <p className="text-xs text-text3 font-mono">RFID: {sow.rfid_tag}</p>
              )}
            </div>
            <div className="text-right">
              <div className="text-3xl font-extrabold font-mono text-primary">{sow.parity}산</div>
              <div className="text-xs text-text3 mt-0.5">산차</div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 mt-5 pt-5 border-t border-border">
            <InfoCell label="품종" value={sow.breed ?? "-"} />
            <InfoCell label="입식 구분" value={sow.entry_type} />
            <InfoCell label="입식일" value={sow.entry_date.slice(0, 10)} mono />
          </div>
        </div>

        {/* 다음 예정 이벤트 (farm_config 기준) */}
        {nextEvent && (
          <div className="bg-primary/5 border border-primary/20 rounded-2xl px-5 py-4 mb-5 flex items-center justify-between">
            <div>
              <div className="text-[11px] text-primary font-bold uppercase tracking-wide">다음 예정</div>
              <div className="text-sm font-semibold text-text mt-0.5">{nextEvent.label}</div>
            </div>
            <div className="text-right font-mono text-sm font-bold text-primary">
              {nextEvent.date ?? "—"}
            </div>
          </div>
        )}

        {/* 산차별 성적 */}
        {timeline.some((t) => t.farrowing) && (
          <div className="mb-5">
            <h2 className="text-sm font-bold mb-3 text-text2">산차별 성적</h2>
            <div className="border border-border rounded-xl overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-bg2 text-text3 text-[11px] uppercase tracking-wide">
                    <th className="text-left font-semibold px-3 py-2">사이클</th>
                    <th className="text-left font-semibold px-3 py-2">교배일</th>
                    <th className="text-left font-semibold px-3 py-2">분만일</th>
                    <th className="text-right font-semibold px-3 py-2">총산</th>
                    <th className="text-right font-semibold px-3 py-2">생존</th>
                    <th className="text-right font-semibold px-3 py-2">이유</th>
                    <th className="text-right font-semibold px-3 py-2">이유일령</th>
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
          <h2 className="text-sm font-bold mb-3 text-text2">번식 이력</h2>

          {timeline.length === 0 ? (
            <div className="bg-surface border border-border rounded-xl p-8 text-center text-text3 text-sm">
              기록된 번식 이력이 없습니다.
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
                        {mating.mating_date.slice(0, 7)} 교배 사이클
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        weaning ? "bg-green-50 text-green-600" :
                        farrowing ? "bg-amber-50 text-amber-600" :
                        "bg-blue-50 text-blue-600"
                      }`}>
                        {weaning ? "이유 완료" : farrowing ? "포유 중" : "임신 중"}
                      </span>
                      <button
                        onClick={() => deleteLatest({ mating, farrowing, weaning })}
                        className="text-[10px] font-semibold text-danger border border-red-200 rounded-md px-2 py-0.5 hover:bg-red-50"
                      >
                        최근 삭제
                      </button>
                    </div>
                  </div>

                  {/* 이벤트 스텝 */}
                  <div className="flex items-start gap-0">
                    {/* 교배 */}
                    <Step
                      icon="💉"
                      label="교배"
                      date={mating.mating_date}
                      detail={mating.mating_type === "AI" ? "인공수정" : "자연교배"}
                      done
                    />
                    <StepConnector done={!!farrowing} />

                    {/* 분만 */}
                    <Step
                      icon="🐖"
                      label="분만"
                      date={farrowing?.farrowing_date}
                      detail={farrowing ? `생존 ${farrowing.born_alive}두 / 사산 ${farrowing.stillborn}두` : undefined}
                      done={!!farrowing}
                    />
                    <StepConnector done={!!weaning} />

                    {/* 이유 */}
                    <Step
                      icon="🌱"
                      label="이유"
                      date={weaning?.weaning_date}
                      detail={weaning ? `${weaning.weaned_count}두 이유` : undefined}
                      done={!!weaning}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
    </div>
  );
}

function computeNextEvent(
  status: string,
  lastMating: string | undefined,
  lastFarrowing: string | undefined,
  lastWeaning: string | undefined,
  cfg: { gestation_days: number; lactation_days: number; wei_target_days: number } | undefined,
): { label: string; date: string | null } | null {
  if (status === "GILT") return { label: "초교배 권장", date: null };
  if (!cfg) return null;
  const addDays = (iso: string, d: number): string => {
    const x = new Date(iso);
    x.setDate(x.getDate() + d);
    return x.toISOString().slice(0, 10);
  };
  if (status === "PREGNANT" && lastMating)
    return { label: "분만 예정", date: addDays(lastMating, cfg.gestation_days) };
  if (status === "LACTATING" && lastFarrowing)
    return { label: "이유 예정", date: addDays(lastFarrowing, cfg.lactation_days) };
  if (status === "OPEN" && lastWeaning)
    return { label: "재교배 예정", date: addDays(lastWeaning, cfg.wei_target_days) };
  if (status === "ACCIDENT") return { label: "재교배 필요", date: null };
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
  icon: string;
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

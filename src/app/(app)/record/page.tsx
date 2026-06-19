"use client";

import { useState, useMemo, useEffect } from "react";
import { useTranslations } from "next-intl";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, PiggyBank } from "lucide-react";
import { eventsApi } from "@/lib/api/endpoints/events";
import { sowsApi } from "@/lib/api/endpoints/sows";
import {
  farrowingSchema, weaningSchema, matingSchema, cullSchema, pigletEventSchema, firstError,
} from "@/lib/validation/eventSchemas";
import { RecentEventsSection } from "@/components/RecentEventsSection";
import { InsightBanner } from "@/components/InsightBanner";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import type {
  Sow,
  SowStatus,
  CreateMatingRequest,
  CreateFarrowingRequest,
  CreateWeaningRequest,
  CreateReproductiveEventRequest,
  SowCullRequest,
  CreatePigletEventRequest,
  EventInsight,
} from "@/types/api.types";

// ─── Constants ────────────────────────────────────────────────────────────────

type EventType = "farrowing" | "mating" | "weaning" | "repro" | "cull" | "piglet_death";

// label은 record.tabXxx 키로 해석
const EVENT_TYPES: { value: EventType; labelKey: string; color: string; bg: string }[] = [
  { value: "farrowing",    labelKey: "tabFarrowing",   color: "#0E9F6E", bg: "#0E9F6E18" },
  { value: "mating",       labelKey: "tabMating",      color: "#2563EB", bg: "#2563EB18" },
  { value: "weaning",      labelKey: "tabWeaning",     color: "#D97706", bg: "#D9770618" },
  { value: "repro",        labelKey: "tabRepro",       color: "#7C3AED", bg: "#7C3AED18" },
  { value: "cull",         labelKey: "tabCull",        color: "#DC2626", bg: "#DC262618" },
  { value: "piglet_death", labelKey: "tabPigletDeath", color: "#9D174D", bg: "#9D174D18" },
];

const STATUS_BADGE: Record<SowStatus, string> = {
  GILT:      "bg-cyan-50 text-cyan-600 border-cyan-100",
  OPEN:      "bg-blue-50 text-blue-600 border-blue-100",
  PREGNANT:  "bg-purple-50 text-purple-600 border-purple-100",
  LACTATING: "bg-green-50 text-green-600 border-green-100",
  ACCIDENT:  "bg-orange-50 text-orange-600 border-orange-100",
  CULLED:    "bg-red-50 text-red-500 border-red-100",
  DEAD:      "bg-gray-100 text-gray-400 border-gray-200",
  SOLD:      "bg-emerald-50 text-emerald-600 border-emerald-100",
  TRANSFER:  "bg-amber-50 text-amber-600 border-amber-100",
};

// ─── Stepper ──────────────────────────────────────────────────────────────────

function Stepper({
  label, sub, value, onChange, colorClass = "text-text",
  min = 0, max = 40,
}: {
  label: string; sub?: string; value: number;
  onChange: (v: number) => void; colorClass?: string;
  min?: number; max?: number;
}) {
  return (
    <div className="flex items-center justify-between py-3.5 px-1">
      <div>
        <div className="text-sm font-semibold text-text">{label}</div>
        {sub && <div className="text-[11px] text-text3 mt-0.5">{sub}</div>}
      </div>
      <div className="flex items-center gap-3.5">
        <button
          type="button"
          onClick={() => onChange(Math.max(min, value - 1))}
          className="w-11 h-11 rounded-xl border border-border bg-surface text-text2 text-xl font-semibold flex items-center justify-center hover:bg-border transition"
        >−</button>
        <input
          type="text"
          inputMode="numeric"
          value={value}
          onChange={(e) => {
            const digits = e.target.value.replace(/[^0-9]/g, "");
            const n = digits === "" ? min : Math.min(max, Math.max(min, parseInt(digits, 10)));
            onChange(n);
          }}
          onFocus={(e) => e.target.select()}
          aria-label={label}
          data-testid={`stepper-${label}`}
          className={`w-[56px] text-center text-[28px] font-bold font-mono tracking-tight bg-transparent outline-none focus:ring-2 focus:ring-primary/30 rounded-lg ${colorClass}`}
        />
        <button
          type="button"
          onClick={() => onChange(Math.min(max, value + 1))}
          className="w-11 h-11 rounded-xl bg-navy text-white text-xl font-semibold flex items-center justify-center hover:opacity-90 transition"
        >+</button>
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

const PAGE_SIZE = 50;

export default function RecordPage() {
  const t = useTranslations("record");
  const tStatus = useTranslations("sowStatus");
  const farmId = useAuthStore((s) => s.activeFarmId);
  const [selectedSow, setSelectedSow] = useState<Sow | null>(null);
  const [eventType, setEventType] = useState<EventType>("farrowing");
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [visible, setVisible] = useState(PAGE_SIZE);
  const [doneIds, setDoneIds] = useState<Set<string>>(new Set());
  const [lastSaved, setLastSaved] = useState<string | null>(null);
  const [lastInsights, setLastInsights] = useState<EventInsight[]>([]);

  // 검색어 디바운스 → 서버사이드 검색 (500개 캡 너머 모돈도 검색됨)
  useEffect(() => {
    const id = setTimeout(() => { setDebounced(search.trim()); setVisible(PAGE_SIZE); }, 300);
    return () => clearTimeout(id);
  }, [search]);

  const { data: sowData } = useQuery({
    queryKey: queryKeys.sows.list(farmId ?? "", { search: debounced }),
    queryFn: () => sowsApi.list(farmId!, { per_page: 200, search: debounced || undefined }),
    enabled: !!farmId,
  });

  const allSows = useMemo(() => sowData?.items ?? [], [sowData]);
  const sows = useMemo(() => allSows.slice(0, visible), [allSows, visible]);
  const hasMore = allSows.length > visible;

  const handleSaved = (msg: string, sowId: string, goNext: boolean, insights?: EventInsight[]) => {
    setDoneIds((prev) => new Set([...prev, sowId]));
    setLastSaved(msg);
    setLastInsights(insights ?? []);   // 인사이트는 다음 저장 전까지 유지(경고 놓치지 않게)
    if (goNext) {
      const currentIndex = sows.findIndex((s) => s.id === sowId);
      const next = sows[currentIndex + 1];
      setSelectedSow(next ?? null);
    }
    setTimeout(() => setLastSaved(null), 3000);
  };

  if (!farmId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text3">{t("selectFarm")}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col md:flex-row h-[calc(100vh-3.5rem)] pb-16 md:pb-0">
      {/* ── LEFT: Sow list ───────────────────────────────────────── */}
      <div className="w-full md:w-72 shrink-0 flex flex-col max-h-[38vh] md:max-h-none border-b md:border-b-0 md:border-r border-border bg-surface">
        <div className="px-4 py-3 border-b border-border">
          <h1 className="text-sm font-extrabold tracking-tight mb-2">{t("eventRecord")}</h1>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t("searchPlaceholder")}
            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm outline-none focus:border-primary transition"
          />
        </div>
        <div className="flex-1 overflow-y-auto">
          {sows.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-text3 text-xs gap-2">
              <PiggyBank size={28} className="text-text3" />
              <span>{t("emptyNoSows")}</span>
            </div>
          ) : (
            sows.map((sow) => {
              const isSelected = selectedSow?.id === sow.id;
              const isDone = doneIds.has(sow.id);
              return (
                <button
                  key={sow.id}
                  onClick={() => { setSelectedSow(sow); setLastInsights([]); }}
                  className={`w-full flex items-center gap-3 px-4 py-3 border-b border-border text-left transition ${
                    isSelected
                      ? "bg-primary/5 border-l-2 border-l-primary"
                      : "hover:bg-background"
                  }`}
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-[10px] font-bold font-mono shrink-0 ${
                    isDone ? "bg-green-100 text-green-600" : "bg-navy/10 text-navy"
                  }`}>
                    {isDone ? <Check size={14} /> : sow.ear_tag.slice(0, 2)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-bold font-mono text-text truncate">{sow.ear_tag}</div>
                    <div className="text-[11px] text-text3">{t("paritySuffix", { n: sow.parity })}</div>
                  </div>
                  <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${STATUS_BADGE[sow.status]}`}>
                    {tStatus(sow.status)}
                  </span>
                </button>
              );
            })
          )}
          {hasMore && (
            <button
              onClick={() => setVisible((v) => v + PAGE_SIZE)}
              className="w-full py-2.5 text-xs font-semibold text-primary hover:bg-primary/5 transition border-b border-border"
            >
              {t("loadMore", { n: allSows.length - visible })}
            </button>
          )}
        </div>
        <div className="px-4 py-2 border-t border-border">
          <p className="text-[11px] text-text3 font-mono">{t("doneCount", { done: doneIds.size, total: allSows.length })}</p>
        </div>
      </div>

      {/* ── RIGHT: Event drawer ──────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">
        {lastSaved && (
          <div className="mx-6 mt-4 px-4 py-2.5 bg-green-50 border border-green-200 rounded-xl text-sm text-green-700 font-medium flex items-center gap-1.5">
            <Check size={15} /> {lastSaved}
          </div>
        )}
        {/* 경고/위험 인사이트는 다음 저장/모돈전환 전까지 유지(놓치지 않게) */}
        {lastInsights.length > 0 && (
          <div className="mx-6 mt-2">
            <InsightBanner insights={lastInsights} />
          </div>
        )}
        {/* 이상 없으면 작은 정상요약만 (저장 직후 3초) */}
        {lastSaved && lastInsights.length === 0 && (
          <div className="mx-6 mt-2">
            <InsightBanner insights={[]} savedNoIssue />
          </div>
        )}

        {!selectedSow ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center px-6">
            <div className="w-16 h-16 rounded-2xl bg-surface border border-border flex items-center justify-center text-text3"><PiggyBank size={28} /></div>
            <div>
              <p className="text-base font-bold text-text1">{t("selectSowTitle")}</p>
              <p className="text-xs text-text3 mt-1">{t("selectSowDesc")}</p>
            </div>
            {/* 입력 가능한 이벤트 미리보기 — 모돈 선택 후 활성화됨 */}
            <div className="flex flex-wrap gap-2 justify-center max-w-md mt-1">
              {EVENT_TYPES.map((et) => (
                <span
                  key={et.value}
                  className="px-3 py-1.5 rounded-full text-xs font-semibold border"
                  style={{ background: et.bg, borderColor: et.color, color: et.color }}
                >
                  {t(et.labelKey)}
                </span>
              ))}
            </div>
            <p className="text-[11px] text-text3 mt-1">{t("selectSowHint")}</p>
          </div>
        ) : (
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Sow header */}
            <div className="px-6 py-4 border-b border-border flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-navy/10 flex items-center justify-center font-bold font-mono text-navy text-sm">
                {selectedSow.ear_tag.slice(0, 2)}
              </div>
              <div className="flex-1">
                <div className="text-base font-extrabold font-mono tracking-tight">{selectedSow.ear_tag}</div>
                <div className="text-xs text-text3">{t("paritySuffix", { n: selectedSow.parity })} · <span className={`font-semibold ${STATUS_BADGE[selectedSow.status].split(" ")[1]}`}>{tStatus(selectedSow.status)}</span></div>
              </div>
              <button
                onClick={() => setSelectedSow(null)}
                className="w-8 h-8 rounded-lg border border-border flex items-center justify-center text-text3 hover:bg-border transition text-sm"
              >✕</button>
            </div>

            {/* Event type chips */}
            <div className="px-6 py-3 border-b border-border flex gap-2 flex-wrap">
              {EVENT_TYPES.map((et) => (
                <button
                  key={et.value}
                  onClick={() => setEventType(et.value)}
                  data-testid={`event-tab-${et.value}`}
                  style={eventType === et.value
                    ? { background: et.bg, borderColor: et.color, color: et.color }
                    : undefined
                  }
                  className={`px-3.5 py-1.5 rounded-full text-xs font-semibold border transition ${
                    eventType === et.value
                      ? "border-current"
                      : "border-border bg-surface text-text3 hover:bg-border"
                  }`}
                >
                  {t(et.labelKey)}
                </button>
              ))}
            </div>

            {/* Form area */}
            <div className="flex-1 overflow-y-auto px-6 py-4">
              {eventType === "farrowing" && (
                <FarrowingPanel
                  farmId={farmId}
                  sow={selectedSow}
                  onSaved={handleSaved}
                />
              )}
              {eventType === "mating" && (
                <MatingPanel farmId={farmId} sow={selectedSow} onSaved={handleSaved} />
              )}
              {eventType === "weaning" && (
                <WeaningPanel farmId={farmId} sow={selectedSow} onSaved={handleSaved} />
              )}
              {eventType === "repro" && (
                <ReproPanel farmId={farmId} sow={selectedSow} onSaved={handleSaved} />
              )}
              {eventType === "cull" && (
                <CullPanel farmId={farmId} sow={selectedSow} onSaved={handleSaved} />
              )}
              {eventType === "piglet_death" && (
                <PigletDeathPanel farmId={farmId} sow={selectedSow} onSaved={handleSaved} />
              )}

              <RecentEventsSection farmId={farmId} sowId={selectedSow.id} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Farrowing Panel ──────────────────────────────────────────────────────────

function FarrowingPanel({ farmId, sow, onSaved }: PanelProps) {
  const t = useTranslations("record");
  const tv = useTranslations("validation");
  const [total, setTotal] = useState(0);
  const [still, setStill] = useState(0);
  const [mummy, setMummy] = useState(0);
  const [weight, setWeight] = useState(1.4);
  const [unit, setUnit] = useState<"kg" | "lbs">("kg");
  const [difficulty, setDifficulty] = useState<"NORMAL" | "ASSISTED" | "DIFFICULT">("NORMAL");
  const [date, setDate] = useState(today());
  const [error, setError] = useState<string | null>(null);

  const alive = Math.max(0, total - still - mummy);
  const hasError = (still + mummy) > total;

  const mutation = useMutation({
    mutationFn: (goNext: boolean) =>
      eventsApi.farrowings.create(farmId, {
        sow_id: sow.id,
        farrowing_date: date,
        born_alive: alive,
        stillborn: still,
        mummified: mummy,
        notes: difficulty !== "NORMAL" ? t("noteDifficulty", { d: difficulty }) : undefined,
      } as CreateFarrowingRequest).then((resp) => ({ goNext, insights: resp.insights })),
    onSuccess: ({ goNext, insights }) => {
      onSaved(t("savedFarrowing", { tag: sow.ear_tag, n: alive }), sow.id, goNext, insights);
      setTotal(0); setStill(0); setMummy(0); setWeight(1.4);
      setDifficulty("NORMAL"); setDate(today()); setError(null);
    },
    onError: (err: unknown) => setError(apiError(err, t("errGeneric"))),
  });

  function submit(goNext: boolean) {
    const err = firstError(farrowingSchema, {
      farrowing_date: date, total_born: total, born_alive: alive,
      stillborn: still, mummified: mummy, avg_birth_weight_kg: weight,
    }, tv);
    if (err) { setError(err); return; }
    mutation.mutate(goNext);
  }

  return (
    <div className="max-w-lg">
      {/* Date */}
      <div className="flex items-center gap-3 mb-4">
        <label className="text-xs font-semibold text-text3 w-16 shrink-0">{t("farrowDate")}</label>
        <input
          type="date" value={date}
          onChange={(e) => setDate(e.target.value)}
          className="input flex-1"
        />
      </div>

      {/* Steppers */}
      <div className="bg-surface border border-border rounded-2xl px-4 divide-y divide-border mb-3">
        <Stepper label={t("totalBorn")} sub="Total born" value={total} onChange={setTotal} max={35} />
        <Stepper label={t("stillborn")} sub="Stillborn" value={still} onChange={setStill} colorClass="text-danger" />
        <Stepper label={t("mummified")} sub="Mummified" value={mummy} onChange={setMummy} colorClass="text-warning" />
      </div>

      {/* Auto-calc born alive */}
      <div className={`rounded-2xl px-5 py-4 flex items-center justify-between mb-3 ${
        hasError
          ? "bg-red-50 border border-red-200"
          : "bg-green-50 border border-green-100"
      }`}>
        <div>
          <div className={`text-xs font-bold font-mono tracking-wider ${hasError ? "text-danger" : "text-success"}`}>
            {t("bornAliveAuto")}
          </div>
          <div className="text-[11px] text-text3 mt-0.5">
            {hasError ? t("errExceed") : t("formula")}
          </div>
        </div>
        <span className={`text-[40px] font-extrabold font-mono tracking-tight ${hasError ? "text-danger" : "text-success"}`}>
          {alive}
        </span>
      </div>

      {/* Birth weight */}
      <div className="bg-surface border border-border rounded-2xl px-5 py-3.5 flex items-center justify-between mb-3">
        <div>
          <div className="text-sm font-semibold text-text">{t("avgBirthWeight")}</div>
          <div className="text-[11px] text-text3 mt-0.5">Avg birth weight</div>
        </div>
        <div className="flex items-center gap-3">
          <button type="button" onClick={() => setWeight((w) => Math.max(0, +(w - 0.1).toFixed(1)))}
            className="w-10 h-10 rounded-xl border border-border bg-background text-text2 text-lg flex items-center justify-center hover:bg-border transition">−</button>
          <span className="min-w-[52px] text-center text-xl font-bold font-mono">{weight.toFixed(1)}</span>
          <button type="button" onClick={() => setWeight((w) => +(w + 0.1).toFixed(1))}
            className="w-10 h-10 rounded-xl border border-border bg-background text-text2 text-lg flex items-center justify-center hover:bg-border transition">+</button>
          <div className="flex bg-background rounded-lg overflow-hidden border border-border">
            {(["kg", "lbs"] as const).map((u) => (
              <button key={u} type="button" onClick={() => setUnit(u)}
                className={`px-3 py-1.5 text-xs font-bold font-mono transition ${unit === u ? "bg-navy text-white" : "text-text3"}`}>{u}</button>
            ))}
          </div>
        </div>
      </div>

      {/* Difficulty */}
      <div className="mb-4">
        <div className="text-xs font-semibold text-text3 mb-2">{t("difficulty")}</div>
        <div className="flex gap-2">
          {([["NORMAL", t("diffNormal")], ["ASSISTED", t("diffAssisted")], ["DIFFICULT", t("diffDifficult")]] as const).map(([k, l]) => (
            <button key={k} type="button" onClick={() => setDifficulty(k)}
              className={`flex-1 py-2.5 rounded-xl border text-sm font-semibold transition ${
                difficulty === k
                  ? "bg-navy text-white border-navy"
                  : "bg-surface border-border text-text2 hover:bg-border"
              }`}>{l}</button>
          ))}
        </div>
      </div>

      {/* Cross-foster */}
      <button type="button"
        className="w-full bg-blue-50 border border-dashed border-blue-200 rounded-2xl px-4 py-3 flex items-center gap-3 mb-5 hover:bg-blue-100 transition">
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-white text-sm font-bold">+</div>
        <div className="flex-1 text-left">
          <div className="text-sm font-semibold text-primary">{t("fosterTitle")}</div>
          <div className="text-[11px] text-text3 mt-0.5">{t("fosterDesc")}</div>
        </div>
        <span className="text-primary text-xs">›</span>
      </button>

      {error && <p className="text-xs text-danger mb-3">{error}</p>}
      <SaveFooter disabled={hasError || total === 0} loading={mutation.isPending} onSave={() => submit(false)} onSaveNext={() => submit(true)} />
    </div>
  );
}

// ─── Mating Panel ─────────────────────────────────────────────────────────────

function MatingPanel({ farmId, sow, onSaved }: PanelProps) {
  const t = useTranslations("record");
  const tv = useTranslations("validation");
  const [form, setForm] = useState<CreateMatingRequest>({
    sow_id: sow.id, mating_date: today(), mating_type: "AI", semen_batch: "", notes: "",
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (goNext: boolean) =>
      eventsApi.matings.create(farmId, { ...form, sow_id: sow.id }).then((resp) => ({ goNext, insights: resp.insights })),
    onSuccess: ({ goNext, insights }) => {
      onSaved(t("savedMating", { tag: sow.ear_tag }), sow.id, goNext, insights);
      setForm({ sow_id: sow.id, mating_date: today(), mating_type: "AI", semen_batch: "", notes: "" });
      setError(null);
    },
    onError: (err: unknown) => setError(apiError(err, t("errGeneric"))),
  });

  function submit(goNext: boolean) {
    const err = firstError(matingSchema, { mating_date: form.mating_date }, tv);
    if (err) { setError(err); return; }
    mutation.mutate(goNext);
  }

  return (
    <div className="max-w-lg space-y-4">
      <Field label={t("matingDate")}>
        <input type="date" value={form.mating_date}
          onChange={(e) => setForm((f) => ({ ...f, mating_date: e.target.value }))}
          className="input" />
      </Field>
      <Field label={t("matingMethod")}>
        <select value={form.mating_type}
          onChange={(e) => setForm((f) => ({ ...f, mating_type: e.target.value as "AI" | "NATURAL" }))}
          className="input">
          <option value="AI">{t("methodAI")}</option>
          <option value="NATURAL">{t("methodNatural")}</option>
        </select>
      </Field>
      <Field label={t("semenNo")}>
        <input value={form.semen_batch ?? ""}
          onChange={(e) => setForm((f) => ({ ...f, semen_batch: e.target.value }))}
          placeholder={t("phSemen")} className="input" />
      </Field>
      <Field label={t("note")}>
        <input value={form.notes ?? ""}
          onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
          className="input" />
      </Field>
      {error && <p className="text-xs text-danger">{error}</p>}
      <SaveFooter disabled={false} loading={mutation.isPending}
        onSave={() => submit(false)} onSaveNext={() => submit(true)} />
    </div>
  );
}

// ─── Weaning Panel ────────────────────────────────────────────────────────────

function WeaningPanel({ farmId, sow, onSaved }: PanelProps) {
  const t = useTranslations("record");
  const tv = useTranslations("validation");
  const [count, setCount] = useState(0);
  const [weight, setWeight] = useState("");
  const [date, setDate] = useState(today());
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (goNext: boolean) =>
      eventsApi.weanings.create(farmId, {
        sow_id: sow.id, weaning_date: date, weaned_count: count,
        avg_weaning_weight_kg: weight ? Number(weight) : undefined,
      } as CreateWeaningRequest).then((resp) => ({ goNext, insights: resp.insights })),
    onSuccess: ({ goNext, insights }) => {
      onSaved(t("savedWeaning", { tag: sow.ear_tag, n: count }), sow.id, goNext, insights);
      setCount(0); setWeight(""); setDate(today()); setError(null);
    },
    onError: (err: unknown) => setError(apiError(err, t("errGeneric"))),
  });

  function submit(goNext: boolean) {
    const err = firstError(weaningSchema, {
      weaning_date: date, weaned_count: count,
      avg_weaning_weight_kg: weight ? Number(weight) : undefined,
    }, tv);
    if (err) { setError(err); return; }
    mutation.mutate(goNext);
  }

  return (
    <div className="max-w-lg">
      <Field label={t("weaningDate")}>
        <input type="date" value={date}
          onChange={(e) => setDate(e.target.value)} className="input mb-4" />
      </Field>
      <div className="bg-surface border border-border rounded-2xl px-4 divide-y divide-border mb-4">
        <Stepper label={t("weanedCount")} sub="Weaned count" value={count} onChange={setCount} colorClass="text-warning" />
      </div>
      <Field label={t("avgWeanWeight")}>
        <input type="number" step="0.1" min={0} value={weight}
          onChange={(e) => setWeight(e.target.value)}
          placeholder={t("phWeanWeight")} className="input" />
      </Field>
      {error && <p className="text-xs text-danger mt-3">{error}</p>}
      <div className="mt-5">
        <SaveFooter disabled={count < 1} loading={mutation.isPending}
          onSave={() => submit(false)} onSaveNext={() => submit(true)} />
      </div>
    </div>
  );
}

// ─── Repro Panel ──────────────────────────────────────────────────────────────

const REPRO_TYPE_KEYS = [
  { value: "RETURN_TO_ESTRUS", key: "rRTS" },
  { value: "ABORTION",         key: "rAbortion" },
  { value: "EMPTY",            key: "rEmpty" },
  { value: "INFERTILE",        key: "rInfertile" },
  { value: "HEAT_DETECTED",    key: "rHeat" },
];

function ReproPanel({ farmId, sow, onSaved }: PanelProps) {
  const t = useTranslations("record");
  const [form, setForm] = useState<CreateReproductiveEventRequest>({
    sow_id: sow.id, event_type: "RETURN_TO_ESTRUS", event_date: today(),
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (goNext: boolean) =>
      eventsApi.reproductive.create(farmId, { ...form, sow_id: sow.id }).then(() => goNext),
    onSuccess: (goNext) => {
      const k = REPRO_TYPE_KEYS.find((x) => x.value === form.event_type)?.key;
      const label = k ? t(k) : "";
      onSaved(t("savedRepro", { tag: sow.ear_tag, label }), sow.id, goNext);
      setForm({ sow_id: sow.id, event_type: "RETURN_TO_ESTRUS", event_date: today() });
      setError(null);
    },
    onError: (err: unknown) => setError(apiError(err, t("errGeneric"))),
  });

  return (
    <div className="max-w-lg space-y-4">
      <p className="text-xs text-text3">{t("reproDesc")}</p>
      <Field label={t("eventType")}>
        <select value={form.event_type}
          onChange={(e) => setForm((f) => ({ ...f, event_type: e.target.value as CreateReproductiveEventRequest["event_type"] }))}
          className="input">
          {REPRO_TYPE_KEYS.map((rt) => <option key={rt.value} value={rt.value}>{t(rt.key)}</option>)}
        </select>
      </Field>
      <Field label={t("eventDate")}>
        <input type="date" value={form.event_date}
          onChange={(e) => setForm((f) => ({ ...f, event_date: e.target.value }))}
          className="input" />
      </Field>
      {error && <p className="text-xs text-danger">{error}</p>}
      <SaveFooter disabled={false} loading={mutation.isPending}
        onSave={() => mutation.mutate(false)} onSaveNext={() => mutation.mutate(true)} />
    </div>
  );
}

// ─── Cull Panel ───────────────────────────────────────────────────────────────

const REMOVAL_TYPE_KEYS = [
  { value: "CULLED",   key: "rmCulled" },
  { value: "DEAD",     key: "rmDead" },
  { value: "SOLD",     key: "rmSold" },
  { value: "TRANSFER", key: "rmTransfer" },
];

const REASON_CATEGORY_KEYS = [
  { value: "REPRODUCTIVE", key: "rcReproductive" },
  { value: "LAMENESS",     key: "rcLameness" },
  { value: "DISEASE",      key: "rcDisease" },
  { value: "AGE",          key: "rcAge" },
  { value: "PERFORMANCE",  key: "rcPerformance" },
  { value: "INJURY",       key: "rcInjury" },
  { value: "BEHAVIOR",     key: "rcBehavior" },
  { value: "UNKNOWN",      key: "rcUnknown" },
  { value: "OTHER",        key: "rcOther" },
];

function CullPanel({ farmId, sow, onSaved }: PanelProps) {
  const t = useTranslations("record");
  const tv = useTranslations("validation");
  const tStatus = useTranslations("sowStatus");
  const queryClient = useQueryClient();
  const [form, setForm] = useState<SowCullRequest>({
    removal_type: "CULLED",
    removal_date: today(),
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (goNext: boolean) =>
      sowsApi.cull(farmId, sow.id, form).then(() => goNext),
    onSuccess: (goNext) => {
      const label = tStatus(form.removal_type);
      onSaved(t("savedCull", { tag: sow.ear_tag, label }), sow.id, goNext);
      queryClient.invalidateQueries({ queryKey: queryKeys.sows.list(farmId, {}) });
      setForm({ removal_type: "CULLED", removal_date: today() });
      setError(null);
    },
    onError: (err: unknown) => setError(apiError(err, t("errGeneric"))),
  });

  function submit(goNext: boolean) {
    const err = firstError(cullSchema, {
      removal_type: form.removal_type, removal_date: form.removal_date,
    }, tv);
    if (err) { setError(err); return; }
    mutation.mutate(goNext);
  }

  return (
    <div className="max-w-lg space-y-4">
      <div className="bg-red-50 border border-red-100 rounded-xl px-4 py-3 text-xs text-red-600">
        {t("cullWarn")}
      </div>
      <Field label={t("removalType")}>
        <select value={form.removal_type}
          onChange={(e) => setForm((f) => ({ ...f, removal_type: e.target.value as SowCullRequest["removal_type"] }))}
          className="input">
          {REMOVAL_TYPE_KEYS.map((r) => <option key={r.value} value={r.value}>{t(r.key)}</option>)}
        </select>
      </Field>
      <Field label={t("removalDate")}>
        <input type="date" value={form.removal_date}
          onChange={(e) => setForm((f) => ({ ...f, removal_date: e.target.value }))}
          className="input" />
      </Field>
      <Field label={t("reasonCat")}>
        <select value={form.reason_category ?? ""}
          onChange={(e) => setForm((f) => ({ ...f, reason_category: (e.target.value || undefined) as SowCullRequest["reason_category"] }))}
          className="input">
          <option value="">{t("selectNone")}</option>
          {REASON_CATEGORY_KEYS.map((r) => <option key={r.value} value={r.value}>{t(r.key)}</option>)}
        </select>
      </Field>
      <Field label={t("reasonDetail")}>
        <input value={form.reason_detail ?? ""}
          onChange={(e) => setForm((f) => ({ ...f, reason_detail: e.target.value || undefined }))}
          placeholder={t("phReasonDetail")} className="input" />
      </Field>
      {error && <p className="text-xs text-danger">{error}</p>}
      <SaveFooter disabled={!form.removal_date} loading={mutation.isPending}
        onSave={() => submit(false)} onSaveNext={() => submit(true)} />
    </div>
  );
}

// ─── Piglet Death Panel ───────────────────────────────────────────────────────

const PIGLET_DEATH_REASON_KEYS = [
  { value: "CRUSHING",    key: "pcCrushing" },
  { value: "SCOURS",      key: "pcScours" },
  { value: "STARVATION",  key: "pcStarvation" },
  { value: "CONGENITAL",  key: "pcCongenital" },
  { value: "HYPOTHERMIA", key: "pcHypothermia" },
  { value: "OTHER",       key: "pcOther" },
];

function PigletDeathPanel({ farmId, sow, onSaved }: PanelProps) {
  const t = useTranslations("record");
  const tv = useTranslations("validation");
  const queryClient = useQueryClient();
  const [form, setForm] = useState<CreatePigletEventRequest>({
    sow_id: sow.id,
    event_date: today(),
    event_type: "DEATH",
    piglet_count: 1,
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (goNext: boolean) =>
      eventsApi.pigletEvents.create(farmId, { ...form, sow_id: sow.id }).then(() => goNext),
    onSuccess: (goNext) => {
      onSaved(t("savedPigletDeath", { tag: sow.ear_tag, n: form.piglet_count }), sow.id, goNext);
      queryClient.invalidateQueries({ queryKey: queryKeys.sows.list(farmId, {}) });
      setForm({ sow_id: sow.id, event_date: today(), event_type: "DEATH", piglet_count: 1 });
      setError(null);
    },
    onError: (err: unknown) => setError(apiError(err, t("errGeneric"))),
  });

  function submit(goNext: boolean) {
    const err = firstError(pigletEventSchema, {
      event_type: form.event_type, event_date: form.event_date, piglet_count: form.piglet_count,
    }, tv);
    if (err) { setError(err); return; }
    mutation.mutate(goNext);
  }

  return (
    <div className="max-w-lg space-y-4">
      <div className="bg-pink-50 border border-pink-100 rounded-xl px-4 py-3 text-xs text-pink-700">
        {t("pdDesc")}
      </div>
      <Field label={t("deathDate")}>
        <input type="date" value={form.event_date}
          onChange={(e) => setForm((f) => ({ ...f, event_date: e.target.value }))}
          className="input" />
      </Field>
      <Field label={t("deathCount")}>
        <Stepper label="" value={form.piglet_count} onChange={(v) => setForm((f) => ({ ...f, piglet_count: v }))}
          min={1} max={30} colorClass="text-danger" />
      </Field>
      <Field label={t("deathCause")}>
        <select value={form.reason ?? ""}
          onChange={(e) => setForm((f) => ({ ...f, reason: (e.target.value || undefined) as CreatePigletEventRequest["reason"] }))}
          className="input">
          <option value="">{t("selectNone")}</option>
          {PIGLET_DEATH_REASON_KEYS.map((r) => <option key={r.value} value={r.value}>{t(r.key)}</option>)}
        </select>
      </Field>
      <Field label={t("memo")}>
        <input value={form.notes ?? ""}
          onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value || undefined }))}
          placeholder={t("phMemo")} className="input" />
      </Field>
      {error && <p className="text-xs text-danger">{error}</p>}
      <SaveFooter disabled={!form.event_date} loading={mutation.isPending}
        onSave={() => submit(false)} onSaveNext={() => submit(true)} />
    </div>
  );
}

// ─── Shared UI ────────────────────────────────────────────────────────────────

type PanelProps = {
  farmId: string;
  sow: Sow;
  onSaved: (msg: string, sowId: string, goNext: boolean, insights?: EventInsight[]) => void;
};

function SaveFooter({
  disabled, loading, onSave, onSaveNext,
}: { disabled: boolean; loading: boolean; onSave: () => void; onSaveNext: () => void }) {
  const t = useTranslations("record");
  return (
    <div className="flex gap-2 pt-2">
      <button
        type="button"
        disabled={disabled || loading}
        onClick={onSave}
        data-testid="event-save"
        className="flex-1 bg-surface border border-border text-text2 py-3 rounded-xl text-sm font-semibold disabled:opacity-50 hover:bg-border transition"
      >
        {loading ? t("saving") : t("save")}
      </button>
      <button
        type="button"
        disabled={disabled || loading}
        onClick={onSaveNext}
        className="flex-[1.4] bg-success text-white py-3 rounded-xl text-sm font-bold disabled:opacity-50 hover:opacity-90 transition flex items-center justify-center gap-2"
      >
        {t("saveNext")}
      </button>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-text3 mb-1.5">{label}</label>
      {children}
    </div>
  );
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function apiError(err: unknown, fallback: string): string {
  const detail = (err as { response?: { data?: { detail?: string | { msg: string }[] } } })
    ?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join(", ");
  return fallback;
}

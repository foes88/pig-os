"use client";

import { useState, useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { eventsApi } from "@/lib/api/endpoints/events";
import { sowsApi } from "@/lib/api/endpoints/sows";
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
} from "@/types/api.types";

// ─── Constants ────────────────────────────────────────────────────────────────

type EventType = "farrowing" | "mating" | "weaning" | "repro" | "cull";

const EVENT_TYPES: { value: EventType; label: string; color: string; bg: string }[] = [
  { value: "farrowing", label: "분만",   color: "#0E9F6E", bg: "#0E9F6E18" },
  { value: "mating",    label: "교배",   color: "#2563EB", bg: "#2563EB18" },
  { value: "weaning",   label: "이유",   color: "#D97706", bg: "#D9770618" },
  { value: "repro",     label: "임신사고", color: "#7C3AED", bg: "#7C3AED18" },
  { value: "cull",      label: "도폐사", color: "#DC2626", bg: "#DC262618" },
];

const STATUS_BADGE: Record<SowStatus, string> = {
  ACTIVE:    "bg-blue-50 text-blue-600 border-blue-100",
  GESTATING: "bg-purple-50 text-purple-600 border-purple-100",
  LACTATING: "bg-green-50 text-green-600 border-green-100",
  WEANED:    "bg-amber-50 text-amber-700 border-amber-100",
  DRY:       "bg-gray-100 text-gray-500 border-gray-200",
  CULLED:    "bg-red-50 text-red-500 border-red-100",
  DEAD:      "bg-gray-100 text-gray-400 border-gray-200",
};

const STATUS_KO: Record<SowStatus, string> = {
  ACTIVE: "공태", GESTATING: "임신", LACTATING: "포유",
  WEANED: "이유", DRY: "건유", CULLED: "도태", DEAD: "폐사",
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
        <span className={`min-w-[42px] text-center text-[28px] font-bold font-mono tracking-tight ${colorClass}`}>
          {value}
        </span>
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

export default function RecordPage() {
  const farmId = useAuthStore((s) => s.activeFarmId);
  const [selectedSow, setSelectedSow] = useState<Sow | null>(null);
  const [eventType, setEventType] = useState<EventType>("farrowing");
  const [search, setSearch] = useState("");
  const [doneIds, setDoneIds] = useState<Set<string>>(new Set());
  const [lastSaved, setLastSaved] = useState<string | null>(null);

  const { data: sowData } = useQuery({
    queryKey: queryKeys.sows.list(farmId ?? "", {}),
    queryFn: () => sowsApi.list(farmId!, { per_page: 500 }),
    enabled: !!farmId,
  });

  const sows = useMemo(() => {
    const all = sowData?.items ?? [];
    if (!search.trim()) return all;
    return all.filter((s) =>
      s.ear_tag.toLowerCase().includes(search.toLowerCase())
    );
  }, [sowData, search]);

  const handleSaved = (msg: string, sowId: string, goNext: boolean) => {
    setDoneIds((prev) => new Set([...prev, sowId]));
    setLastSaved(msg);
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
        <p className="text-text3">농장을 선택해주세요.</p>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-3.5rem)] pb-16 md:pb-0">
      {/* ── LEFT: Sow list ───────────────────────────────────────── */}
      <div className="w-72 shrink-0 flex flex-col border-r border-border bg-surface">
        <div className="px-4 py-3 border-b border-border">
          <h1 className="text-sm font-extrabold tracking-tight mb-2">이벤트 기록</h1>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="이표 검색..."
            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm outline-none focus:border-primary transition"
          />
        </div>
        <div className="flex-1 overflow-y-auto">
          {sows.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-text3 text-xs gap-2">
              <span className="text-2xl">🐷</span>
              <span>등록된 모돈이 없습니다</span>
            </div>
          ) : (
            sows.map((sow) => {
              const isSelected = selectedSow?.id === sow.id;
              const isDone = doneIds.has(sow.id);
              return (
                <button
                  key={sow.id}
                  onClick={() => setSelectedSow(sow)}
                  className={`w-full flex items-center gap-3 px-4 py-3 border-b border-border text-left transition ${
                    isSelected
                      ? "bg-primary/5 border-l-2 border-l-primary"
                      : "hover:bg-background"
                  }`}
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-[10px] font-bold font-mono shrink-0 ${
                    isDone ? "bg-green-100 text-green-600" : "bg-navy/10 text-navy"
                  }`}>
                    {isDone ? "✓" : sow.ear_tag.slice(0, 2)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-bold font-mono text-text truncate">{sow.ear_tag}</div>
                    <div className="text-[11px] text-text3">{sow.parity}산차</div>
                  </div>
                  <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${STATUS_BADGE[sow.status]}`}>
                    {STATUS_KO[sow.status]}
                  </span>
                </button>
              );
            })
          )}
        </div>
        <div className="px-4 py-2 border-t border-border">
          <p className="text-[11px] text-text3 font-mono">{doneIds.size} / {sows.length} 완료</p>
        </div>
      </div>

      {/* ── RIGHT: Event drawer ──────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">
        {lastSaved && (
          <div className="mx-6 mt-4 px-4 py-2.5 bg-green-50 border border-green-200 rounded-xl text-sm text-green-700 font-medium">
            ✓ {lastSaved}
          </div>
        )}

        {!selectedSow ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center">
            <div className="w-16 h-16 rounded-2xl bg-surface border border-border flex items-center justify-center text-2xl">🐷</div>
            <div>
              <p className="text-base font-bold text-text1">왼쪽에서 모돈을 선택하세요</p>
              <p className="text-xs text-text3 mt-1">또는 이표를 검색해 바로 입력</p>
            </div>
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
                <div className="text-xs text-text3">{selectedSow.parity}산차 · <span className={`font-semibold ${STATUS_BADGE[selectedSow.status].split(" ")[1]}`}>{STATUS_KO[selectedSow.status]}</span></div>
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
                  {et.label}
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
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Farrowing Panel ──────────────────────────────────────────────────────────

function FarrowingPanel({ farmId, sow, onSaved }: PanelProps) {
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
        notes: difficulty !== "NORMAL" ? `난이도: ${difficulty}` : undefined,
      } as CreateFarrowingRequest).then(() => goNext),
    onSuccess: (goNext) => {
      onSaved(`${sow.ear_tag} 분만 기록 완료 (생존 ${alive}두)`, sow.id, goNext);
      setTotal(0); setStill(0); setMummy(0); setWeight(1.4);
      setDifficulty("NORMAL"); setDate(today()); setError(null);
    },
    onError: (err: unknown) => setError(apiError(err)),
  });

  return (
    <div className="max-w-lg">
      {/* Date */}
      <div className="flex items-center gap-3 mb-4">
        <label className="text-xs font-semibold text-text3 w-16 shrink-0">분만일</label>
        <input
          type="date" value={date}
          onChange={(e) => setDate(e.target.value)}
          className="input flex-1"
        />
      </div>

      {/* Steppers */}
      <div className="bg-surface border border-border rounded-2xl px-4 divide-y divide-border mb-3">
        <Stepper label="총산자수" sub="Total born" value={total} onChange={setTotal} max={35} />
        <Stepper label="사산" sub="Stillborn" value={still} onChange={setStill} colorClass="text-danger" />
        <Stepper label="미라" sub="Mummified" value={mummy} onChange={setMummy} colorClass="text-warning" />
      </div>

      {/* Auto-calc born alive */}
      <div className={`rounded-2xl px-5 py-4 flex items-center justify-between mb-3 ${
        hasError
          ? "bg-red-50 border border-red-200"
          : "bg-green-50 border border-green-100"
      }`}>
        <div>
          <div className={`text-xs font-bold font-mono tracking-wider ${hasError ? "text-danger" : "text-success"}`}>
            실산자수 (자동계산)
          </div>
          <div className="text-[11px] text-text3 mt-0.5">
            {hasError ? "사산+미라가 총산자를 초과합니다" : "총산자 − 사산 − 미라"}
          </div>
        </div>
        <span className={`text-[40px] font-extrabold font-mono tracking-tight ${hasError ? "text-danger" : "text-success"}`}>
          {alive}
        </span>
      </div>

      {/* Birth weight */}
      <div className="bg-surface border border-border rounded-2xl px-5 py-3.5 flex items-center justify-between mb-3">
        <div>
          <div className="text-sm font-semibold text-text">평균 생시체중</div>
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
        <div className="text-xs font-semibold text-text3 mb-2">분만 난이도</div>
        <div className="flex gap-2">
          {([["NORMAL","정상"],["ASSISTED","도움"],["DIFFICULT","난산"]] as const).map(([k, l]) => (
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
          <div className="text-sm font-semibold text-primary">양자 조정 기록</div>
          <div className="text-[11px] text-text3 mt-0.5">대리모로 자돈 이동 시 — PSY 정확도에 반영됩니다</div>
        </div>
        <span className="text-primary text-xs">›</span>
      </button>

      {error && <p className="text-xs text-danger mb-3">{error}</p>}
      <SaveFooter disabled={hasError || total === 0} loading={mutation.isPending} onSave={() => mutation.mutate(false)} onSaveNext={() => mutation.mutate(true)} />
    </div>
  );
}

// ─── Mating Panel ─────────────────────────────────────────────────────────────

function MatingPanel({ farmId, sow, onSaved }: PanelProps) {
  const [form, setForm] = useState<CreateMatingRequest>({
    sow_id: sow.id, mating_date: today(), mating_type: "AI", semen_batch: "", notes: "",
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (goNext: boolean) =>
      eventsApi.matings.create(farmId, { ...form, sow_id: sow.id }).then(() => goNext),
    onSuccess: (goNext) => {
      onSaved(`${sow.ear_tag} 교배 기록 완료`, sow.id, goNext);
      setForm({ sow_id: sow.id, mating_date: today(), mating_type: "AI", semen_batch: "", notes: "" });
      setError(null);
    },
    onError: (err: unknown) => setError(apiError(err)),
  });

  return (
    <div className="max-w-lg space-y-4">
      <Field label="교배일 *">
        <input type="date" value={form.mating_date}
          onChange={(e) => setForm((f) => ({ ...f, mating_date: e.target.value }))}
          className="input" />
      </Field>
      <Field label="교배 방법">
        <select value={form.mating_type}
          onChange={(e) => setForm((f) => ({ ...f, mating_type: e.target.value as "AI" | "NATURAL" }))}
          className="input">
          <option value="AI">인공수정 (AI)</option>
          <option value="NATURAL">자연교배</option>
        </select>
      </Field>
      <Field label="정액 번호">
        <input value={form.semen_batch ?? ""}
          onChange={(e) => setForm((f) => ({ ...f, semen_batch: e.target.value }))}
          placeholder="예: SB-2024-001" className="input" />
      </Field>
      <Field label="비고">
        <input value={form.notes ?? ""}
          onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
          className="input" />
      </Field>
      {error && <p className="text-xs text-danger">{error}</p>}
      <SaveFooter disabled={false} loading={mutation.isPending}
        onSave={() => mutation.mutate(false)} onSaveNext={() => mutation.mutate(true)} />
    </div>
  );
}

// ─── Weaning Panel ────────────────────────────────────────────────────────────

function WeaningPanel({ farmId, sow, onSaved }: PanelProps) {
  const [count, setCount] = useState(0);
  const [weight, setWeight] = useState("");
  const [date, setDate] = useState(today());
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (goNext: boolean) =>
      eventsApi.weanings.create(farmId, {
        sow_id: sow.id, weaning_date: date, weaned_count: count,
        avg_weaning_weight_kg: weight ? Number(weight) : undefined,
      } as CreateWeaningRequest).then(() => goNext),
    onSuccess: (goNext) => {
      onSaved(`${sow.ear_tag} 이유 기록 완료 (${count}두)`, sow.id, goNext);
      setCount(0); setWeight(""); setDate(today()); setError(null);
    },
    onError: (err: unknown) => setError(apiError(err)),
  });

  return (
    <div className="max-w-lg">
      <Field label="이유일 *">
        <input type="date" value={date}
          onChange={(e) => setDate(e.target.value)} className="input mb-4" />
      </Field>
      <div className="bg-surface border border-border rounded-2xl px-4 divide-y divide-border mb-4">
        <Stepper label="이유두수" sub="Weaned count" value={count} onChange={setCount} colorClass="text-warning" />
      </div>
      <Field label="평균 이유체중 (kg)">
        <input type="number" step="0.1" min={0} value={weight}
          onChange={(e) => setWeight(e.target.value)}
          placeholder="예: 7.5" className="input" />
      </Field>
      {error && <p className="text-xs text-danger mt-3">{error}</p>}
      <div className="mt-5">
        <SaveFooter disabled={count < 1} loading={mutation.isPending}
          onSave={() => mutation.mutate(false)} onSaveNext={() => mutation.mutate(true)} />
      </div>
    </div>
  );
}

// ─── Repro Panel ──────────────────────────────────────────────────────────────

const REPRO_TYPES = [
  { value: "RETURN_TO_ESTRUS", label: "반발정" },
  { value: "ABORTION",         label: "유산" },
  { value: "EMPTY",            label: "공태 확인" },
  { value: "INFERTILE",        label: "불임" },
  { value: "HEAT_DETECTED",    label: "발정 감지" },
];

function ReproPanel({ farmId, sow, onSaved }: PanelProps) {
  const [form, setForm] = useState<CreateReproductiveEventRequest>({
    sow_id: sow.id, event_type: "RETURN_TO_ESTRUS", event_date: today(),
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (goNext: boolean) =>
      eventsApi.reproductive.create(farmId, { ...form, sow_id: sow.id }).then(() => goNext),
    onSuccess: (goNext) => {
      const label = REPRO_TYPES.find((t) => t.value === form.event_type)?.label ?? "";
      onSaved(`${sow.ear_tag} ${label} 기록 완료`, sow.id, goNext);
      setForm({ sow_id: sow.id, event_type: "RETURN_TO_ESTRUS", event_date: today() });
      setError(null);
    },
    onError: (err: unknown) => setError(apiError(err)),
  });

  return (
    <div className="max-w-lg space-y-4">
      <p className="text-xs text-text3">반발정·유산·공태 등 비생산 이벤트 — NPD 계산에 반영됩니다</p>
      <Field label="이벤트 유형 *">
        <select value={form.event_type}
          onChange={(e) => setForm((f) => ({ ...f, event_type: e.target.value as CreateReproductiveEventRequest["event_type"] }))}
          className="input">
          {REPRO_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
      </Field>
      <Field label="발생일 *">
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

const CULL_REASONS = [
  { value: "CULLED", label: "도태 (저생산성/노령/지제불량 등)" },
  { value: "DEAD",   label: "폐사" },
  { value: "SOLD",   label: "판매" },
];

function CullPanel({ farmId, sow, onSaved }: PanelProps) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<SowCullRequest>({ reason: "CULLED", event_date: today() });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (goNext: boolean) =>
      sowsApi.cull(farmId, sow.id, form).then(() => goNext),
    onSuccess: (goNext) => {
      const label = CULL_REASONS.find((r) => r.value === form.reason)?.label.split(" ")[0] ?? "";
      onSaved(`${sow.ear_tag} ${label} 처리 완료`, sow.id, goNext);
      queryClient.invalidateQueries({ queryKey: queryKeys.sows.list(farmId, {}) });
      setForm({ reason: "CULLED", event_date: today() });
      setError(null);
    },
    onError: (err: unknown) => setError(apiError(err)),
  });

  return (
    <div className="max-w-lg space-y-4">
      <div className="bg-red-50 border border-red-100 rounded-xl px-4 py-3 text-xs text-red-600">
        처리 후 모돈은 비활성화됩니다
      </div>
      <Field label="처리 유형 *">
        <select value={form.reason}
          onChange={(e) => setForm((f) => ({ ...f, reason: e.target.value as SowCullRequest["reason"] }))}
          className="input">
          {CULL_REASONS.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
        </select>
      </Field>
      <Field label="처리일 *">
        <input type="date" value={form.event_date}
          onChange={(e) => setForm((f) => ({ ...f, event_date: e.target.value }))}
          className="input" />
      </Field>
      <Field label="사유">
        <input value={form.cull_reason ?? ""}
          onChange={(e) => setForm((f) => ({ ...f, cull_reason: e.target.value }))}
          placeholder="예: 8산 이상 노령, 지제 불량" className="input" />
      </Field>
      {error && <p className="text-xs text-danger">{error}</p>}
      <SaveFooter disabled={false} loading={mutation.isPending}
        onSave={() => mutation.mutate(false)} onSaveNext={() => mutation.mutate(true)} />
    </div>
  );
}

// ─── Shared UI ────────────────────────────────────────────────────────────────

type PanelProps = {
  farmId: string;
  sow: Sow;
  onSaved: (msg: string, sowId: string, goNext: boolean) => void;
};

function SaveFooter({
  disabled, loading, onSave, onSaveNext,
}: { disabled: boolean; loading: boolean; onSave: () => void; onSaveNext: () => void }) {
  return (
    <div className="flex gap-2 pt-2">
      <button
        type="button"
        disabled={disabled || loading}
        onClick={onSave}
        className="flex-1 bg-surface border border-border text-text2 py-3 rounded-xl text-sm font-semibold disabled:opacity-50 hover:bg-border transition"
      >
        {loading ? "저장 중..." : "저장"}
      </button>
      <button
        type="button"
        disabled={disabled || loading}
        onClick={onSaveNext}
        className="flex-[1.4] bg-success text-white py-3 rounded-xl text-sm font-bold disabled:opacity-50 hover:opacity-90 transition flex items-center justify-center gap-2"
      >
        저장 후 다음 모돈 →
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

function apiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: string | { msg: string }[] } } })
    ?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join(", ");
  return "요청 처리 중 오류가 발생했습니다.";
}

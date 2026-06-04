"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { eventsApi } from "@/lib/api/endpoints/events";
import { sowsApi } from "@/lib/api/endpoints/sows";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import type {
  CreateMatingRequest,
  CreateFarrowingRequest,
  CreateWeaningRequest,
  CreateReproductiveEventRequest,
  SowCullRequest,
} from "@/types/api.types";

type Tab = "mating" | "farrowing" | "weaning" | "repro" | "cull";

const TABS: { value: Tab; label: string; icon: string }[] = [
  { value: "mating",    label: "교배",    icon: "💉" },
  { value: "farrowing", label: "분만",    icon: "🐖" },
  { value: "weaning",   label: "이유",    icon: "🌱" },
  { value: "repro",     label: "임신사고", icon: "⚠️" },
  { value: "cull",      label: "도폐사",  icon: "📋" },
];

export default function RecordPage() {
  const farmId = useAuthStore((s) => s.activeFarmId);
  const [tab, setTab] = useState<Tab>("mating");
  const [success, setSuccess] = useState<string | null>(null);

  const { data: sowData } = useQuery({
    queryKey: queryKeys.sows.list(farmId ?? "", {}),
    queryFn: () => sowsApi.list(farmId!, { per_page: 200 }),
    enabled: !!farmId,
  });
  const sows = sowData?.items ?? [];

  if (!farmId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text3">농장을 선택해주세요.</p>
      </div>
    );
  }

  return (
    <div className="p-7 max-w-2xl">
        <div className="mb-6">
          <h1 className="text-[22px] font-extrabold tracking-tight">이벤트 기록</h1>
          <p className="text-xs text-text3 mt-0.5">교배 · 분만 · 이유 실적 입력</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {TABS.map((t) => (
            <button
              key={t.value}
              onClick={() => { setTab(t.value); setSuccess(null); }}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition ${
                tab === t.value
                  ? "bg-primary text-white shadow-md"
                  : "bg-surface border border-border text-text2 hover:bg-border"
              }`}
            >
              <span>{t.icon}</span> {t.label}
            </button>
          ))}
        </div>

        {success && (
          <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3 mb-4 text-sm text-green-700 font-medium">
            ✓ {success}
          </div>
        )}

        <div className="bg-surface border border-border rounded-2xl p-6">
          {tab === "mating" && (
            <MatingForm farmId={farmId} sows={sows} onSuccess={(msg) => setSuccess(msg)} />
          )}
          {tab === "farrowing" && (
            <FarrowingForm farmId={farmId} sows={sows} onSuccess={(msg) => setSuccess(msg)} />
          )}
          {tab === "weaning" && (
            <WeaningForm farmId={farmId} sows={sows} onSuccess={(msg) => setSuccess(msg)} />
          )}
          {tab === "repro" && (
            <ReproForm farmId={farmId} sows={sows} onSuccess={(msg) => setSuccess(msg)} />
          )}
          {tab === "cull" && (
            <CullForm farmId={farmId} sows={sows} onSuccess={(msg) => setSuccess(msg)} />
          )}
        </div>
    </div>
  );
}

// ── Mating Form ───────────────────────────────────────────────────────────────

function MatingForm({
  farmId, sows, onSuccess,
}: { farmId: string; sows: { id: string; ear_tag: string }[]; onSuccess: (msg: string) => void }) {
  const [form, setForm] = useState<CreateMatingRequest>({
    sow_id: "",
    mating_date: today(),
    mating_type: "AI",
    semen_batch: "",
    notes: "",
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => eventsApi.matings.create(farmId, form),
    onSuccess: () => {
      onSuccess(`${tagOf(sows, form.sow_id)} 교배 기록 완료`);
      setForm({ sow_id: "", mating_date: today(), mating_type: "AI", semen_batch: "", notes: "" });
      setError(null);
    },
    onError: (err: unknown) => setError(apiError(err)),
  });

  return (
    <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-4">
      <h2 className="text-base font-bold mb-2">💉 교배 기록</h2>
      <Field label="모돈 *">
        <SowSelect sows={sows} value={form.sow_id} onChange={(v) => setForm((f) => ({ ...f, sow_id: v }))} />
      </Field>
      <Field label="교배일 *">
        <input type="date" value={form.mating_date} onChange={(e) => setForm((f) => ({ ...f, mating_date: e.target.value }))} className="input" />
      </Field>
      <Field label="교배 방법">
        <select value={form.mating_type} onChange={(e) => setForm((f) => ({ ...f, mating_type: e.target.value as "AI" | "NATURAL" }))} className="input">
          <option value="AI">인공수정 (AI)</option>
          <option value="NATURAL">자연교배</option>
        </select>
      </Field>
      <Field label="정액 번호">
        <input value={form.semen_batch ?? ""} onChange={(e) => setForm((f) => ({ ...f, semen_batch: e.target.value }))} placeholder="예: SB-2024-001" className="input" />
      </Field>
      <Field label="비고">
        <input value={form.notes ?? ""} onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} className="input" />
      </Field>
      {error && <p className="text-xs text-red-500">{error}</p>}
      <SubmitBtn disabled={!form.sow_id} loading={mutation.isPending} label="교배 기록" />
    </form>
  );
}

// ── Farrowing Form ────────────────────────────────────────────────────────────

function FarrowingForm({
  farmId, sows, onSuccess,
}: { farmId: string; sows: { id: string; ear_tag: string }[]; onSuccess: (msg: string) => void }) {
  const [form, setForm] = useState({
    sow_id: "",
    mating_id: "",
    farrowing_date: today(),
    born_alive: 0,
    stillborn: 0,
    mummified: 0,
    notes: "",
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => eventsApi.farrowings.create(farmId, {
      sow_id: form.sow_id,
      farrowing_date: form.farrowing_date,
      born_alive: form.born_alive,
      stillborn: form.stillborn,
      mummified: form.mummified,
      notes: form.notes,
    } as CreateFarrowingRequest),
    onSuccess: () => {
      onSuccess(`${tagOf(sows, form.sow_id)} 분만 기록 완료 (생존 ${form.born_alive}두)`);
      setForm({ sow_id: "", mating_id: "", farrowing_date: today(), born_alive: 0, stillborn: 0, mummified: 0, notes: "" });
      setError(null);
    },
    onError: (err: unknown) => setError(apiError(err)),
  });

  const total = form.born_alive + form.stillborn + form.mummified;

  return (
    <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-4">
      <h2 className="text-base font-bold mb-2">🐖 분만 기록</h2>
      <Field label="모돈 *">
        <SowSelect sows={sows} value={form.sow_id} onChange={(v) => setForm((f) => ({ ...f, sow_id: v }))} />
      </Field>
      <Field label="분만일 *">
        <input type="date" value={form.farrowing_date} onChange={(e) => setForm((f) => ({ ...f, farrowing_date: e.target.value }))} className="input" />
      </Field>
      <div className="grid grid-cols-3 gap-3">
        <Field label="생존두수 *">
          <input type="number" min={0} value={form.born_alive} onChange={(e) => setForm((f) => ({ ...f, born_alive: Number(e.target.value) }))} className="input" />
        </Field>
        <Field label="사산">
          <input type="number" min={0} value={form.stillborn} onChange={(e) => setForm((f) => ({ ...f, stillborn: Number(e.target.value) }))} className="input" />
        </Field>
        <Field label="미라">
          <input type="number" min={0} value={form.mummified} onChange={(e) => setForm((f) => ({ ...f, mummified: Number(e.target.value) }))} className="input" />
        </Field>
      </div>
      <div className="text-xs text-text3 -mt-2">총 출생 = <span className="font-bold text-text1">{total}두</span></div>
      <Field label="비고">
        <input value={form.notes} onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} className="input" />
      </Field>
      {error && <p className="text-xs text-red-500">{error}</p>}
      <SubmitBtn disabled={!form.sow_id || form.born_alive < 0} loading={mutation.isPending} label="분만 기록" />
    </form>
  );
}

// ── Weaning Form ──────────────────────────────────────────────────────────────

function WeaningForm({
  farmId, sows, onSuccess,
}: { farmId: string; sows: { id: string; ear_tag: string }[]; onSuccess: (msg: string) => void }) {
  const [form, setForm] = useState({
    sow_id: "",
    weaning_date: today(),
    weaned_count: 0,
    avg_weight_kg: "",
    notes: "",
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => eventsApi.weanings.create(farmId, {
      sow_id: form.sow_id,
      weaning_date: form.weaning_date,
      weaned_count: form.weaned_count,
      avg_weaning_weight_kg: form.avg_weight_kg ? Number(form.avg_weight_kg) : undefined,
      notes: form.notes,
    } as CreateWeaningRequest),
    onSuccess: () => {
      onSuccess(`${tagOf(sows, form.sow_id)} 이유 기록 완료 (${form.weaned_count}두)`);
      setForm({ sow_id: "", weaning_date: today(), weaned_count: 0, avg_weight_kg: "", notes: "" });
      setError(null);
    },
    onError: (err: unknown) => setError(apiError(err)),
  });

  return (
    <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-4">
      <h2 className="text-base font-bold mb-2">🌱 이유 기록</h2>
      <Field label="모돈 *">
        <SowSelect sows={sows} value={form.sow_id} onChange={(v) => setForm((f) => ({ ...f, sow_id: v }))} />
      </Field>
      <Field label="이유일 *">
        <input type="date" value={form.weaning_date} onChange={(e) => setForm((f) => ({ ...f, weaning_date: e.target.value }))} className="input" />
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="이유두수 *">
          <input type="number" min={0} value={form.weaned_count} onChange={(e) => setForm((f) => ({ ...f, weaned_count: Number(e.target.value) }))} className="input" />
        </Field>
        <Field label="평균체중 (kg)">
          <input type="number" step="0.1" min={0} value={form.avg_weight_kg} onChange={(e) => setForm((f) => ({ ...f, avg_weight_kg: e.target.value }))} placeholder="예: 7.5" className="input" />
        </Field>
      </div>
      <Field label="비고">
        <input value={form.notes} onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} className="input" />
      </Field>
      {error && <p className="text-xs text-red-500">{error}</p>}
      <SubmitBtn disabled={!form.sow_id || form.weaned_count < 1} loading={mutation.isPending} label="이유 기록" />
    </form>
  );
}

// ── Repro Form (임신사고) ─────────────────────────────────────────────────────

const REPRO_TYPES: { value: string; label: string }[] = [
  { value: "RETURN_TO_ESTRUS", label: "반발정" },
  { value: "ABORTION",         label: "유산" },
  { value: "EMPTY",            label: "공태 확인" },
  { value: "INFERTILE",        label: "불임" },
  { value: "HEAT_DETECTED",    label: "발정 감지" },
];

function ReproForm({
  farmId, sows, onSuccess,
}: { farmId: string; sows: { id: string; ear_tag: string }[]; onSuccess: (msg: string) => void }) {
  const [form, setForm] = useState<CreateReproductiveEventRequest>({
    sow_id: "", event_type: "RETURN_TO_ESTRUS", event_date: today(),
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => eventsApi.reproductive.create(farmId, form),
    onSuccess: () => {
      const label = REPRO_TYPES.find((t) => t.value === form.event_type)?.label ?? form.event_type;
      onSuccess(`${tagOf(sows, form.sow_id)} ${label} 기록 완료`);
      setForm({ sow_id: "", event_type: "RETURN_TO_ESTRUS", event_date: today() });
      setError(null);
    },
    onError: (err: unknown) => setError(apiError(err)),
  });

  return (
    <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-4">
      <h2 className="text-base font-bold mb-2">⚠️ 임신사고 기록</h2>
      <p className="text-xs text-text3 -mt-2">반발정·유산·공태 등 비생산 이벤트 — NPD 계산에 반영됩니다</p>
      <Field label="모돈 *">
        <SowSelect sows={sows} value={form.sow_id} onChange={(v) => setForm((f) => ({ ...f, sow_id: v }))} />
      </Field>
      <Field label="이벤트 유형 *">
        <select value={form.event_type} onChange={(e) => setForm((f) => ({ ...f, event_type: e.target.value as CreateReproductiveEventRequest["event_type"] }))} className="input">
          {REPRO_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
      </Field>
      <Field label="발생일 *">
        <input type="date" value={form.event_date} onChange={(e) => setForm((f) => ({ ...f, event_date: e.target.value }))} className="input" />
      </Field>
      <Field label="비고">
        <input value={form.notes ?? ""} onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} className="input" />
      </Field>
      {error && <p className="text-xs text-red-500">{error}</p>}
      <SubmitBtn disabled={!form.sow_id} loading={mutation.isPending} label="임신사고 기록" />
    </form>
  );
}

// ── Cull Form (도폐사) ────────────────────────────────────────────────────────

const CULL_REASONS: { value: string; label: string }[] = [
  { value: "CULLED", label: "도태 (저생산성/노령/지제불량 등)" },
  { value: "DEAD",   label: "폐사" },
  { value: "SOLD",   label: "판매" },
];

function CullForm({
  farmId, sows, onSuccess,
}: { farmId: string; sows: { id: string; ear_tag: string }[]; onSuccess: (msg: string) => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<SowCullRequest>({
    reason: "CULLED", event_date: today(),
  });
  const [sowId, setSowId] = useState("");
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => sowsApi.cull(farmId, sowId, form),
    onSuccess: () => {
      const label = CULL_REASONS.find((r) => r.value === form.reason)?.label.split(" ")[0] ?? form.reason;
      onSuccess(`${tagOf(sows, sowId)} ${label} 처리 완료`);
      queryClient.invalidateQueries({ queryKey: ["sows", farmId] });
      setSowId("");
      setForm({ reason: "CULLED", event_date: today() });
      setError(null);
    },
    onError: (err: unknown) => setError(apiError(err)),
  });

  return (
    <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-4">
      <h2 className="text-base font-bold mb-2">📋 도폐사 기록</h2>
      <p className="text-xs text-text3 -mt-2">처리 후 모돈은 비활성화됩니다</p>
      <Field label="모돈 *">
        <SowSelect sows={sows} value={sowId} onChange={setSowId} />
      </Field>
      <Field label="처리 유형 *">
        <select value={form.reason} onChange={(e) => setForm((f) => ({ ...f, reason: e.target.value as SowCullRequest["reason"] }))} className="input">
          {CULL_REASONS.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
        </select>
      </Field>
      <Field label="처리일 *">
        <input type="date" value={form.event_date} onChange={(e) => setForm((f) => ({ ...f, event_date: e.target.value }))} className="input" />
      </Field>
      <Field label="사유">
        <input value={form.cull_reason ?? ""} onChange={(e) => setForm((f) => ({ ...f, cull_reason: e.target.value }))} placeholder="예: 8산 이상 노령, 지제 불량" className="input" />
      </Field>
      {error && <p className="text-xs text-red-500">{error}</p>}
      <SubmitBtn disabled={!sowId} loading={mutation.isPending} label="도폐사 처리" />
    </form>
  );
}

// ── Shared components ─────────────────────────────────────────────────────────

function SowSelect({ sows, value, onChange }: { sows: { id: string; ear_tag: string }[]; value: string; onChange: (v: string) => void }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} className="input">
      <option value="">모돈 선택...</option>
      {sows.map((s) => (
        <option key={s.id} value={s.id}>{s.ear_tag}</option>
      ))}
    </select>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-medium text-text2 mb-1">{label}</label>
      {children}
    </div>
  );
}

function SubmitBtn({ disabled, loading, label }: { disabled: boolean; loading: boolean; label: string }) {
  return (
    <button
      type="submit"
      disabled={disabled || loading}
      className="w-full bg-primary text-white py-2.5 rounded-xl text-sm font-semibold mt-2 disabled:opacity-50 transition hover:bg-primary/90"
    >
      {loading ? "저장 중..." : label}
    </button>
  );
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function tagOf(sows: { id: string; ear_tag: string }[], id: string) {
  return sows.find((s) => s.id === id)?.ear_tag ?? id;
}

function apiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: string | { msg: string }[] } } })
    ?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join(", ");
  return "요청 처리 중 오류가 발생했습니다.";
}

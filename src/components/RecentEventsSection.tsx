"use client";

import { useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Trash2, X } from "lucide-react";
import { eventsApi } from "@/lib/api/endpoints/events";
import { queryKeys } from "@/lib/api/queryKeys";
import type {
  Farrowing,
  Mating,
  UpdateFarrowingRequest,
  UpdateMatingRequest,
  UpdateWeaningRequest,
  Weaning,
} from "@/types/api.types";

type Kind = "mating" | "farrowing" | "weaning";

interface UnifiedEvent {
  kind: Kind;
  id: string;
  date: string;
  summary: string;
  raw: Mating | Farrowing | Weaning;
}

const KIND_STYLE: Record<Kind, string> = {
  mating: "bg-green-soft text-success border-success/30",
  farrowing: "bg-green-50 text-green-700 border-green-200",
  weaning: "bg-amber-50 text-amber-700 border-amber-200",
};

/**
 * 선택한 모돈의 최근 번식 이벤트(교배/분만/이유) 이력 + 수정/삭제.
 * record 페이지와 모돈 상세 페이지에서 공용.
 */
export function RecentEventsSection({
  farmId,
  sowId,
  limit = 5,
  onChanged,
}: {
  farmId: string;
  sowId: string;
  limit?: number;
  onChanged?: () => void;
}) {
  const t = useTranslations("eventHistory");
  const qc = useQueryClient();
  const [editing, setEditing] = useState<UnifiedEvent | null>(null);
  const [confirmDel, setConfirmDel] = useState<UnifiedEvent | null>(null);

  const matings = useQuery({
    queryKey: queryKeys.events.matings(farmId, sowId),
    queryFn: () => eventsApi.matings.list(farmId, sowId),
    enabled: !!farmId && !!sowId,
  });
  const farrowings = useQuery({
    queryKey: queryKeys.events.farrowings(farmId, sowId),
    queryFn: () => eventsApi.farrowings.list(farmId, sowId),
    enabled: !!farmId && !!sowId,
  });
  const weanings = useQuery({
    queryKey: queryKeys.events.weanings(farmId, sowId),
    queryFn: () => eventsApi.weanings.list(farmId, sowId),
    enabled: !!farmId && !!sowId,
  });

  const events = useMemo<UnifiedEvent[]>(() => {
    const out: UnifiedEvent[] = [];
    (matings.data ?? []).forEach((m) =>
      out.push({ kind: "mating", id: m.id, date: m.mating_date, raw: m,
        summary: `${m.mating_type}${m.mating_number ? ` #${m.mating_number}` : ""}` }));
    (farrowings.data ?? []).forEach((f) =>
      out.push({ kind: "farrowing", id: f.id, date: f.farrowing_date, raw: f,
        summary: `TB ${f.total_born} · BA ${f.born_alive}` }));
    (weanings.data ?? []).forEach((w) =>
      out.push({ kind: "weaning", id: w.id, date: w.weaning_date, raw: w,
        summary: `${t("weaned")} ${w.weaned_count}` }));
    return out.sort((a, b) => (a.date < b.date ? 1 : -1)).slice(0, limit);
  }, [matings.data, farrowings.data, weanings.data, limit, t]);

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: queryKeys.events.matings(farmId, sowId) });
    qc.invalidateQueries({ queryKey: queryKeys.events.farrowings(farmId, sowId) });
    qc.invalidateQueries({ queryKey: queryKeys.events.weanings(farmId, sowId) });
    qc.invalidateQueries({ queryKey: queryKeys.sows.detail(farmId, sowId) });
    onChanged?.();
  };

  const del = useMutation({
    mutationFn: (e: UnifiedEvent) => {
      if (e.kind === "mating") return eventsApi.matings.remove(farmId, e.id);
      if (e.kind === "farrowing") return eventsApi.farrowings.remove(farmId, e.id);
      return eventsApi.weanings.remove(farmId, e.id);
    },
    onSuccess: () => { setConfirmDel(null); invalidate(); },
  });

  const isLoading = matings.isLoading || farrowings.isLoading || weanings.isLoading;

  return (
    <div className="mt-5 border-t border-border pt-4">
      <h3 className="text-xs font-bold text-text2 mb-2">{t("title")}</h3>

      {isLoading && <div className="text-xs text-text3 py-3">{t("loading")}</div>}
      {!isLoading && events.length === 0 && (
        <div className="text-xs text-text3 py-3">{t("empty")}</div>
      )}

      <div className="space-y-1.5">
        {events.map((e) => (
          <div key={`${e.kind}-${e.id}`} className="flex items-center gap-2 bg-surface border border-border rounded-lg px-3 py-2">
            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${KIND_STYLE[e.kind]}`}>
              {t(`kind_${e.kind}`)}
            </span>
            <span className="text-xs font-mono text-text2">{e.date}</span>
            <span className="text-xs text-text3 flex-1 truncate">{e.summary}</span>
            <button onClick={() => setEditing(e)} title={t("edit")}
              data-testid={`event-edit-${e.kind}`}
              className="p-1 rounded text-text3 hover:text-primary hover:bg-primary/5 transition">
              <Pencil className="w-3.5 h-3.5" />
            </button>
            <button onClick={() => setConfirmDel(e)} title={t("delete")}
              data-testid={`event-delete-${e.kind}`}
              className="p-1 rounded text-text3 hover:text-danger hover:bg-red-50 transition">
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>

      {editing && (
        <EditModal farmId={farmId} event={editing}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); invalidate(); }} />
      )}

      {confirmDel && (
        <ConfirmDeleteModal
          busy={del.isPending}
          error={del.isError ? t("deleteError") : null}
          onCancel={() => setConfirmDel(null)}
          onConfirm={() => del.mutate(confirmDel)}
        />
      )}
    </div>
  );
}

// ── Edit modal (type-specific fields) ───────────────────────────────────────
function EditModal({
  farmId, event, onClose, onSaved,
}: { farmId: string; event: UnifiedEvent; onClose: () => void; onSaved: () => void }) {
  const t = useTranslations("eventHistory");

  const m = event.kind === "mating" ? (event.raw as Mating) : null;
  const f = event.kind === "farrowing" ? (event.raw as Farrowing) : null;
  const w = event.kind === "weaning" ? (event.raw as Weaning) : null;

  const [matingDate, setMatingDate] = useState(m?.mating_date ?? "");
  const [matingNotes, setMatingNotes] = useState(m?.notes ?? "");

  const [farDate, setFarDate] = useState(f?.farrowing_date ?? "");
  const [ba, setBa] = useState(f?.born_alive ?? 0);
  const [sb, setSb] = useState(f?.stillborn ?? 0);
  const [mum, setMum] = useState(f?.mummified ?? 0);

  const [weanDate, setWeanDate] = useState(w?.weaning_date ?? "");
  const [weaned, setWeaned] = useState(w?.weaned_count ?? 0);
  const [weanWeight, setWeanWeight] = useState(w?.avg_weaning_weight_kg ?? "");

  const [error, setError] = useState<string | null>(null);

  const save = useMutation({
    mutationFn: async (): Promise<void> => {
      if (event.kind === "mating") {
        const body: UpdateMatingRequest = { mating_date: matingDate, notes: matingNotes || null };
        await eventsApi.matings.update(farmId, event.id, body);
        return;
      }
      if (event.kind === "farrowing") {
        const body: UpdateFarrowingRequest = {
          farrowing_date: farDate, born_alive: Number(ba), stillborn: Number(sb), mummified: Number(mum),
        };
        await eventsApi.farrowings.update(farmId, event.id, body);
        return;
      }
      const body: UpdateWeaningRequest = {
        weaning_date: weanDate, weaned_count: Number(weaned),
        avg_weaning_weight_kg: weanWeight === "" ? null : Number(weanWeight),
      };
      await eventsApi.weanings.update(farmId, event.id, body);
    },
    onSuccess: onSaved,
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : t("saveError"));
    },
  });

  return (
    <Modal onClose={onClose} title={`${t(`kind_${event.kind}`)} ${t("edit")}`}>
      <div className="space-y-3">
        {event.kind === "mating" && (
          <>
            <Field label={t("date")}>
              <input type="date" value={matingDate} onChange={(e) => setMatingDate(e.target.value)} className={inputCls} />
            </Field>
            <Field label={t("notes")}>
              <input value={matingNotes} onChange={(e) => setMatingNotes(e.target.value)} className={inputCls} />
            </Field>
          </>
        )}
        {event.kind === "farrowing" && (
          <>
            <Field label={t("date")}>
              <input type="date" value={farDate} onChange={(e) => setFarDate(e.target.value)} className={inputCls} />
            </Field>
            <div className="grid grid-cols-3 gap-2">
              <Field label={t("bornAlive")}>
                <input type="number" min={0} value={ba} onChange={(e) => setBa(+e.target.value)} className={inputCls} />
              </Field>
              <Field label={t("stillborn")}>
                <input type="number" min={0} value={sb} onChange={(e) => setSb(+e.target.value)} className={inputCls} />
              </Field>
              <Field label={t("mummified")}>
                <input type="number" min={0} value={mum} onChange={(e) => setMum(+e.target.value)} className={inputCls} />
              </Field>
            </div>
          </>
        )}
        {event.kind === "weaning" && (
          <>
            <Field label={t("date")}>
              <input type="date" value={weanDate} onChange={(e) => setWeanDate(e.target.value)} className={inputCls} />
            </Field>
            <div className="grid grid-cols-2 gap-2">
              <Field label={t("weanedCount")}>
                <input type="number" min={0} value={weaned} onChange={(e) => setWeaned(+e.target.value)} className={inputCls} />
              </Field>
              <Field label={t("avgWeight")}>
                <input type="number" step="0.1" value={weanWeight}
                  onChange={(e) => setWeanWeight(e.target.value)} className={inputCls} />
              </Field>
            </div>
          </>
        )}

        {error && <div className="text-xs text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}

        <div className="flex gap-2 pt-1">
          <button onClick={onClose} className="flex-1 text-sm border border-border rounded-lg py-2 hover:bg-border transition">
            {t("cancel")}
          </button>
          <button onClick={() => save.mutate()} disabled={save.isPending}
            data-testid="event-edit-save"
            className="flex-1 text-sm font-medium text-white bg-primary rounded-lg py-2 hover:opacity-90 transition disabled:opacity-50">
            {save.isPending ? t("saving") : t("save")}
          </button>
        </div>
      </div>
    </Modal>
  );
}

function ConfirmDeleteModal({
  busy, error, onCancel, onConfirm,
}: { busy: boolean; error: string | null; onCancel: () => void; onConfirm: () => void }) {
  const t = useTranslations("eventHistory");
  return (
    <Modal onClose={onCancel} title={t("deleteConfirmTitle")}>
      <p className="text-sm text-text2 mb-4">{t("deleteConfirmBody")}</p>
      {error && <div className="text-xs text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-3">{error}</div>}
      <div className="flex gap-2">
        <button onClick={onCancel} className="flex-1 text-sm border border-border rounded-lg py-2 hover:bg-border transition">
          {t("cancel")}
        </button>
        <button onClick={onConfirm} disabled={busy}
          data-testid="event-delete-confirm"
          className="flex-1 text-sm font-medium text-white bg-danger rounded-lg py-2 hover:opacity-90 transition disabled:opacity-50">
          {busy ? t("deleting") : t("delete")}
        </button>
      </div>
    </Modal>
  );
}

const inputCls = "w-full border border-border rounded-lg px-2.5 py-1.5 text-sm bg-surface focus:outline-none focus:ring-1 focus:ring-primary";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-[11px] font-medium text-text3 mb-1 block">{label}</span>
      {children}
    </label>
  );
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="bg-background border border-border rounded-2xl w-full max-w-sm p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold">{title}</h2>
          <button onClick={onClose} className="p-1 rounded text-text3 hover:bg-border transition">
            <X className="w-4 h-4" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

"use client";

import { localToday } from "@/lib/date";
import { useState } from "react";
import { useTranslations } from "next-intl";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { finishersApi } from "@/lib/api/endpoints/finishers";
import { useAuthStore } from "@/store/auth.store";
import { canEntry } from "@/lib/auth/permissions";
import { finisherEntrySchema, finisherShipSchema, firstError } from "@/lib/validation/eventSchemas";
import type {
  CreateFinisherGroupRequest,
  FinisherGroup,
  FinisherGroupShipRequest,
  UpdateFinisherGroupRequest,
} from "@/types/api.types";

export default function FinishersPage() {
  const t = useTranslations("finishers");
  const farmId = useAuthStore((s) => s.activeFarmId);
  const role = useAuthStore((s) => s.user?.role);
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [shippingId, setShippingId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [activeOnly, setActiveOnly] = useState(true);
  const [page, setPage] = useState(1);

  const { data: groups = [], isLoading } = useQuery({
    queryKey: ["finishers", farmId, activeOnly],
    queryFn: () => finishersApi.list(farmId!, activeOnly),
    enabled: !!farmId,
  });

  const PER_PAGE = 20;
  const totalPages = Math.max(1, Math.ceil(groups.length / PER_PAGE));
  // 목록이 줄거나(출하/삭제·필터 토글) 현재 page가 범위를 넘으면 빈 화면이 됨 → 클램프(H1).
  const safePage = Math.min(page, totalPages);
  const paged = groups.slice((safePage - 1) * PER_PAGE, safePage * PER_PAGE);

  if (!farmId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text3">{t("selectFarm")}</p>
      </div>
    );
  }

  return (
    <div className="p-7">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[22px] font-extrabold tracking-tight">{t("title")}</h1>
            <p className="text-xs text-text3 mt-0.5">{t("subtitle")}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => { setActiveOnly((v) => !v); setPage(1); }}
              className={`px-3 py-2 rounded-lg text-xs font-medium border transition ${
                activeOnly ? "bg-primary text-white" : "bg-surface border-border text-text2"
              }`}
            >
              {activeOnly ? t("activeOnly") : t("all")}
            </button>
            {canEntry(role) && (
              <button
                onClick={() => setShowForm(true)}
                data-testid="finishers-add-btn"
                className="bg-primary text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-primary/90 transition"
              >
                {t("addGroup")}
              </button>
            )}
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-20 text-text3 text-sm">{t("loading")}</div>
        ) : groups.length === 0 ? (
          <div className="text-center py-20 text-text3 text-sm">
            {activeOnly ? t("emptyActive") : t("emptyAll")}
          </div>
        ) : (
          <div className="grid gap-3">
            {paged.map((g) => {
              const isActive = !g.end_date;
              const mortality = g.head_count_out != null
                ? g.head_count_in - g.head_count_out
                : null;
              return (
                <div key={g.id} className="bg-surface border border-border rounded-xl p-5 flex items-center justify-between">
                  <div className="flex items-center gap-5">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-text1">{g.group_code}</span>
                        {g.batch_name && <span className="text-xs text-text3">— {g.batch_name}</span>}
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          isActive ? "bg-green-50 text-green-600" : "bg-slate-100 text-slate-500"
                        }`}>
                          {isActive ? t("statusActive") : t("statusDone")}
                        </span>
                      </div>
                      <div className="text-xs text-text3 mt-0.5">
                        {t("entryInfo", { date: g.start_date, n: g.head_count_in })}
                        {g.avg_entry_weight_kg && ` · ${t("avgEntryWeight", { w: g.avg_entry_weight_kg })}`}
                      </div>
                    </div>
                    <div className="flex gap-6 text-sm">
                      {g.end_date && (
                        <>
                          <div>
                            <div className="text-[10px] text-text3">{t("shipDate")}</div>
                            <div className="font-medium">{g.end_date}</div>
                          </div>
                          <div>
                            <div className="text-[10px] text-text3">{t("shipHead")}</div>
                            <div className="font-medium">{g.head_count_out}{t("headUnit")}</div>
                          </div>
                          {g.avg_exit_weight_kg && (
                            <div>
                              <div className="text-[10px] text-text3">{t("shipWeight")}</div>
                              <div className="font-medium">{g.avg_exit_weight_kg}kg</div>
                            </div>
                          )}
                          {mortality != null && (
                            <div>
                              <div className="text-[10px] text-text3">{t("mortality")}</div>
                              <div className={`font-medium ${mortality > 0 ? "text-danger" : "text-success"}`}>
                                {Math.max(0, mortality)}{t("headUnit")}
                              </div>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                  {canEntry(role) && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setEditingId(g.id)}
                        className="border border-border text-text2 px-3 py-2 rounded-lg text-xs font-semibold hover:border-primary transition"
                      >
                        {t("edit")}
                      </button>
                      {isActive && (
                        <button
                          onClick={() => setShippingId(g.id)}
                          className="bg-amber-500 text-white px-4 py-2 rounded-lg text-xs font-semibold hover:bg-amber-500/90 transition"
                        >
                          {t("ship")}
                        </button>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-3 text-xs text-text3">
            <span>{t("pageInfo", { n: groups.length, p: safePage, tp: totalPages })}</span>
            <div className="flex gap-1.5">
              <button onClick={() => setPage(Math.max(1, safePage - 1))} disabled={safePage <= 1}
                className="px-2.5 py-1 rounded-md border border-border disabled:opacity-40 hover:border-primary">{t("prev")}</button>
              <button onClick={() => setPage(Math.min(totalPages, safePage + 1))} disabled={safePage >= totalPages}
                className="px-2.5 py-1 rounded-md border border-border disabled:opacity-40 hover:border-primary">{t("next")}</button>
            </div>
          </div>
        )}

      {showForm && (
        <CreateGroupModal
          farmId={farmId}
          onClose={() => setShowForm(false)}
          onSuccess={() => {
            setShowForm(false);
            queryClient.invalidateQueries({ queryKey: ["finishers", farmId] });
          }}
        />
      )}

      {shippingId && (
        <ShipModal
          farmId={farmId}
          groupId={shippingId}
          onClose={() => setShippingId(null)}
          onSuccess={() => {
            setShippingId(null);
            queryClient.invalidateQueries({ queryKey: ["finishers", farmId] });
          }}
        />
      )}

      {editingId && (
        <EditGroupModal
          farmId={farmId}
          group={groups.find((g) => g.id === editingId)!}
          onClose={() => setEditingId(null)}
          onSuccess={() => {
            setEditingId(null);
            queryClient.invalidateQueries({ queryKey: ["finishers", farmId] });
          }}
        />
      )}
    </div>
  );
}

function CreateGroupModal({ farmId, onClose, onSuccess }: { farmId: string; onClose: () => void; onSuccess: () => void }) {
  const t = useTranslations("finishers");
  const tv = useTranslations("validation");
  const [form, setForm] = useState<CreateFinisherGroupRequest>({
    group_code: "",
    start_date: localToday(),
    head_count_in: 0,
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => finishersApi.create(farmId, form),
    onSuccess,
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : t("regFailed"));
    },
  });

  function submit() {
    const err = firstError(finisherEntrySchema, {
      group_code: form.group_code, start_date: form.start_date,
      head_count_in: form.head_count_in, avg_entry_weight_kg: form.avg_entry_weight_kg,
    }, tv);
    if (err) { setError(err); return; }
    mutation.mutate();
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl">
        <h2 className="text-base font-bold mb-4">{t("modalAddTitle")}</h2>
        <div className="space-y-3">
          <Field label={t("fGroupCode")}>
            <input value={form.group_code} onChange={(e) => setForm((f) => ({ ...f, group_code: e.target.value }))}
              placeholder={t("phGroupCode")} data-testid="add-finisher-code" className="input" />
          </Field>
          <Field label={t("fBatchName")}>
            <input value={form.batch_name ?? ""} onChange={(e) => setForm((f) => ({ ...f, batch_name: e.target.value }))}
              placeholder={t("phBatchName")} className="input" />
          </Field>
          <Field label={t("fEntryDate")}>
            <input type="date" value={form.start_date} onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))} className="input" />
          </Field>
          <Field label={t("fHeadIn")}>
            <input type="number" min={1} value={form.head_count_in || ""} onChange={(e) => setForm((f) => ({ ...f, head_count_in: Number(e.target.value) }))} className="input" />
          </Field>
          <Field label={t("fAvgEntryWeight")}>
            <input type="number" step="0.1" min={0} value={form.avg_entry_weight_kg ?? ""} onChange={(e) => setForm((f) => ({ ...f, avg_entry_weight_kg: Number(e.target.value) || undefined }))} placeholder={t("phAvgEntryWeight")} className="input" />
          </Field>
        </div>
        {error && <p className="text-xs text-red-500 mt-3">{error}</p>}
        <div className="flex gap-2 mt-5">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-lg py-2 text-sm">{t("cancel")}</button>
          <button onClick={submit} disabled={!form.group_code || !form.head_count_in || mutation.isPending}
            data-testid="add-finisher-submit"
            className="flex-1 bg-primary text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50">
            {mutation.isPending ? t("regging") : t("reg")}
          </button>
        </div>
      </div>
    </div>
  );
}

function ShipModal({ farmId, groupId, onClose, onSuccess }: { farmId: string; groupId: string; onClose: () => void; onSuccess: () => void }) {
  const t = useTranslations("finishers");
  const tv = useTranslations("validation");
  const [form, setForm] = useState<FinisherGroupShipRequest>({
    end_date: localToday(),
    head_count_out: 0,
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => finishersApi.ship(farmId, groupId, form),
    onSuccess,
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : t("shipFailed"));
    },
  });

  function submit() {
    const err = firstError(finisherShipSchema, {
      end_date: form.end_date, head_count_out: form.head_count_out,
      avg_exit_weight_kg: form.avg_exit_weight_kg,
    }, tv);
    if (err) { setError(err); return; }
    mutation.mutate();
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl">
        <h2 className="text-base font-bold mb-4">{t("modalShipTitle")}</h2>
        <div className="space-y-3">
          <Field label={t("fShipDate")}>
            <input type="date" value={form.end_date} onChange={(e) => setForm((f) => ({ ...f, end_date: e.target.value }))} className="input" />
          </Field>
          <Field label={t("fHeadOut")}>
            <input type="number" min={1} value={form.head_count_out || ""} onChange={(e) => setForm((f) => ({ ...f, head_count_out: Number(e.target.value) }))} className="input" />
          </Field>
          <Field label={t("fAvgExitWeight")}>
            <input type="number" step="0.1" min={0} value={form.avg_exit_weight_kg ?? ""} onChange={(e) => setForm((f) => ({ ...f, avg_exit_weight_kg: Number(e.target.value) || undefined }))} placeholder={t("phAvgExitWeight")} className="input" />
          </Field>
        </div>
        {error && <p className="text-xs text-red-500 mt-3">{error}</p>}
        <div className="flex gap-2 mt-5">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-lg py-2 text-sm">{t("cancel")}</button>
          <button onClick={submit} disabled={!form.head_count_out || mutation.isPending}
            className="flex-1 bg-amber-500 text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50">
            {mutation.isPending ? t("shipping") : t("shipDone")}
          </button>
        </div>
      </div>
    </div>
  );
}

function EditGroupModal({ farmId, group, onClose, onSuccess }: { farmId: string; group: FinisherGroup; onClose: () => void; onSuccess: () => void }) {
  const t = useTranslations("finishers");
  const [form, setForm] = useState<UpdateFinisherGroupRequest>({
    batch_name: group.batch_name ?? "",
    head_count_in: group.head_count_in,
    avg_entry_weight_kg: group.avg_entry_weight_kg ?? undefined,
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => finishersApi.update(farmId, group.id, form),
    onSuccess,
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : t("editFailed"));
    },
  });

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl">
        <h2 className="text-base font-bold mb-1">{t("modalEditTitle")}</h2>
        <p className="text-xs text-gray-400 mb-4 font-mono">{group.group_code}</p>
        <div className="space-y-3">
          <Field label={t("fBatchName")}>
            <input value={form.batch_name ?? ""} onChange={(e) => setForm((f) => ({ ...f, batch_name: e.target.value }))} className="input" />
          </Field>
          <Field label={t("fHeadIn")}>
            <input type="number" min={1} value={form.head_count_in || ""} onChange={(e) => setForm((f) => ({ ...f, head_count_in: Number(e.target.value) }))} className="input" />
          </Field>
          <Field label={t("fAvgEntryWeight")}>
            <input type="number" step="0.1" min={0} value={form.avg_entry_weight_kg ?? ""} onChange={(e) => setForm((f) => ({ ...f, avg_entry_weight_kg: Number(e.target.value) || undefined }))} className="input" />
          </Field>
        </div>
        {error && <p className="text-xs text-red-500 mt-3">{error}</p>}
        <div className="flex gap-2 mt-5">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-lg py-2 text-sm">{t("cancel")}</button>
          <button onClick={() => mutation.mutate()} disabled={!form.head_count_in || mutation.isPending}
            className="flex-1 bg-primary text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50">
            {mutation.isPending ? t("saving") : t("save")}
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      {children}
    </div>
  );
}

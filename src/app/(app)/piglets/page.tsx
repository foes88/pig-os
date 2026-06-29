"use client";

import { localToday } from "@/lib/date";
import { useState } from "react";
import { useTranslations } from "next-intl";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { pigletsApi } from "@/lib/api/endpoints/piglets";
import { useAuthStore } from "@/store/auth.store";
import { canEntry } from "@/lib/auth/permissions";
import { useActiveRole } from "@/lib/auth/useActiveRole";
import type { CreatePigletGroupRequest, PigletGroupTransferOutRequest } from "@/types/api.types";

// 전출 유형 → i18n 키 (piglets.ttXxx)
const TRANSFER_TYPE_KEY: Record<string, string> = {
  FINISHER_TRANSFER: "ttFinisherTransfer",
  SOLD: "ttSold",
  CULLED: "ttCulled",
};

export default function PigletsPage() {
  const t = useTranslations("piglets");
  const farmId = useAuthStore((s) => s.activeFarmId);
  const canWrite = canEntry(useActiveRole());
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [transferId, setTransferId] = useState<string | null>(null);
  const [activeOnly, setActiveOnly] = useState(true);

  const { data: groups = [], isLoading } = useQuery({
    queryKey: ["piglets", farmId, activeOnly],
    queryFn: () => pigletsApi.list(farmId!, activeOnly),
    enabled: !!farmId,
  });

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
              onClick={() => setActiveOnly((v) => !v)}
              className={`px-3 py-2 rounded-lg text-xs font-medium border transition ${
                activeOnly ? "bg-primary text-white" : "bg-surface border-border text-text2"
              }`}
            >
              {activeOnly ? t("activeOnly") : t("all")}
            </button>
            {canWrite && (
              <button
                onClick={() => setShowForm(true)}
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
            {groups.map((g) => {
              const isActive = !g.transfer_date;
              const surviving = g.head_count_in - g.head_count_dead;
              const mortalityRate = g.head_count_in > 0
                ? ((g.head_count_dead / g.head_count_in) * 100).toFixed(1)
                : "0.0";
              return (
                <div key={g.id} className="bg-surface border border-border rounded-xl p-5 flex items-center justify-between">
                  <div className="flex items-center gap-6">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-text1">{g.group_code}</span>
                        {g.batch_name && <span className="text-xs text-text3">— {g.batch_name}</span>}
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          isActive ? "bg-green-soft text-success" : "bg-slate-100 text-slate-500"
                        }`}>
                          {isActive ? t("statusActive") : (TRANSFER_TYPE_KEY[g.transfer_type ?? ""] ? t(TRANSFER_TYPE_KEY[g.transfer_type ?? ""]) : t("statusDone"))}
                        </span>
                      </div>
                      <div className="text-xs text-text3 mt-0.5">
                        {t("weanInfo", { date: g.weaning_date, n: g.head_count_in })}
                        {g.avg_entry_weight_kg && ` · ${t("avgEntryWeight", { w: g.avg_entry_weight_kg })}`}
                      </div>
                    </div>
                    <div className="flex gap-5 text-sm">
                      <div>
                        <div className="text-[10px] text-text3">{t("surviving")}</div>
                        <div className="font-medium font-mono">{surviving}{t("headUnit")}</div>
                      </div>
                      <div>
                        <div className="text-[10px] text-text3">{t("mortalityRate")}</div>
                        <div className={`font-medium font-mono ${Number(mortalityRate) > 5 ? "text-danger" : "text-success"}`}>
                          {mortalityRate}%
                        </div>
                      </div>
                      {!isActive && g.transfer_date && (
                        <div>
                          <div className="text-[10px] text-text3">{t("transferDate")}</div>
                          <div className="font-medium">{g.transfer_date}</div>
                        </div>
                      )}
                    </div>
                  </div>
                  {isActive && canWrite && (
                    <button
                      onClick={() => setTransferId(g.id)}
                      className="bg-success text-white px-4 py-2 rounded-lg text-xs font-semibold hover:bg-success/90 transition"
                    >
                      {t("transferSale")}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}

      {showForm && (
        <CreateGroupModal
          farmId={farmId}
          onClose={() => setShowForm(false)}
          onSuccess={() => {
            setShowForm(false);
            queryClient.invalidateQueries({ queryKey: ["piglets", farmId] });
          }}
        />
      )}

      {transferId && (
        <TransferModal
          farmId={farmId}
          groupId={transferId}
          onClose={() => setTransferId(null)}
          onSuccess={() => {
            setTransferId(null);
            queryClient.invalidateQueries({ queryKey: ["piglets", farmId] });
          }}
        />
      )}
    </div>
  );
}

function CreateGroupModal({ farmId, onClose, onSuccess }: { farmId: string; onClose: () => void; onSuccess: () => void }) {
  const t = useTranslations("piglets");
  const [form, setForm] = useState<CreatePigletGroupRequest>({
    group_code: "",
    weaning_date: localToday(),
    head_count_in: 0,
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => pigletsApi.create(farmId, form),
    onSuccess,
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : t("regFailed"));
    },
  });

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl">
        <h2 className="text-base font-bold mb-4">{t("modalStartTitle")}</h2>
        <div className="space-y-3">
          <Field label={t("fGroupCode")}>
            <input value={form.group_code} onChange={(e) => setForm((f) => ({ ...f, group_code: e.target.value }))}
              placeholder={t("phGroupCode")} className="input" />
          </Field>
          <Field label={t("fBatchName")}>
            <input value={form.batch_name ?? ""} onChange={(e) => setForm((f) => ({ ...f, batch_name: e.target.value }))}
              placeholder={t("phBatchName")} className="input" />
          </Field>
          <Field label={t("fWeanDate")}>
            <input type="date" value={form.weaning_date} onChange={(e) => setForm((f) => ({ ...f, weaning_date: e.target.value }))} className="input" />
          </Field>
          <Field label={t("fHead")}>
            <input type="number" min={1} value={form.head_count_in || ""} onChange={(e) => setForm((f) => ({ ...f, head_count_in: Number(e.target.value) }))} className="input" />
          </Field>
          <Field label={t("fAvgWeanWeight")}>
            <input type="number" step="0.1" min={0} value={form.avg_entry_weight_kg ?? ""} onChange={(e) => setForm((f) => ({ ...f, avg_entry_weight_kg: Number(e.target.value) || undefined }))} placeholder={t("phAvgWeanWeight")} className="input" />
          </Field>
        </div>
        {error && <p className="text-xs text-red-500 mt-3">{error}</p>}
        <div className="flex gap-2 mt-5">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-lg py-2 text-sm">{t("cancel")}</button>
          <button onClick={() => mutation.mutate()} disabled={!form.group_code || !form.head_count_in || mutation.isPending}
            className="flex-1 bg-primary text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50">
            {mutation.isPending ? t("starting") : t("start")}
          </button>
        </div>
      </div>
    </div>
  );
}

function TransferModal({ farmId, groupId, onClose, onSuccess }: { farmId: string; groupId: string; onClose: () => void; onSuccess: () => void }) {
  const t = useTranslations("piglets");
  const [form, setForm] = useState<PigletGroupTransferOutRequest>({
    transfer_date: localToday(),
    transfer_type: "FINISHER_TRANSFER",
    head_count_out: 0,
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => pigletsApi.transferOut(farmId, groupId, form),
    onSuccess,
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : t("processFailed"));
    },
  });

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl">
        <h2 className="text-base font-bold mb-4">{t("modalTransferTitle")}</h2>
        <div className="space-y-3">
          <Field label={t("fTransferType")}>
            <select value={form.transfer_type} onChange={(e) => setForm((f) => ({ ...f, transfer_type: e.target.value as PigletGroupTransferOutRequest["transfer_type"] }))} className="input">
              <option value="FINISHER_TRANSFER">{t("ttFinisherTransfer")}</option>
              <option value="SOLD">{t("ttSold")}</option>
              <option value="CULLED">{t("ttCulled")}</option>
            </select>
          </Field>
          <Field label={t("fProcessDate")}>
            <input type="date" value={form.transfer_date} onChange={(e) => setForm((f) => ({ ...f, transfer_date: e.target.value }))} className="input" />
          </Field>
          <Field label={t("fProcessHead")}>
            <input type="number" min={1} value={form.head_count_out || ""} onChange={(e) => setForm((f) => ({ ...f, head_count_out: Number(e.target.value) }))} className="input" />
          </Field>
          <Field label={t("fAvgWeight")}>
            <input type="number" step="0.1" min={0} value={form.avg_exit_weight_kg ?? ""} onChange={(e) => setForm((f) => ({ ...f, avg_exit_weight_kg: Number(e.target.value) || undefined }))} placeholder={t("phAvgWeight")} className="input" />
          </Field>
        </div>
        {error && <p className="text-xs text-red-500 mt-3">{error}</p>}
        <div className="flex gap-2 mt-5">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-lg py-2 text-sm">{t("cancel")}</button>
          <button onClick={() => mutation.mutate()} disabled={!form.head_count_out || mutation.isPending}
            className="flex-1 bg-success text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50">
            {mutation.isPending ? t("processing") : t("transferDone")}
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

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Pencil, LogOut, X } from "lucide-react";
import { sowsApi } from "@/lib/api/endpoints/sows";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import type {
  Sow,
  SowStatus,
  SowEntryType,
  CreateSowRequest,
  UpdateSowRequest,
  SowCullRequest,
} from "@/types/api.types";

// SCREEN_MENU_SPEC: All / Gilt / Open / Pregnant / Lactating / Accident / Culled
// 라벨은 sowStatus i18n 키로 해석, tabAll은 sows.tabAll
const STATUS_TABS: (SowStatus | "ALL")[] = ["ALL", "GILT", "OPEN", "PREGNANT", "LACTATING", "ACCIDENT", "CULLED"];

// 상태 → 배지 색상 (라벨은 sowStatus 키)
const STATUS_CLS: Record<string, string> = {
  GILT:      "bg-cyan-50 text-cyan-600",
  OPEN:      "bg-slate-100 text-slate-600",
  PREGNANT:  "bg-blue-50 text-blue-600",
  LACTATING: "bg-green-50 text-green-600",
  ACCIDENT:  "bg-orange-50 text-orange-600",
  CULLED:    "bg-red-50 text-red-500",
  DEAD:      "bg-gray-100 text-gray-500",
  SOLD:      "bg-emerald-50 text-emerald-600",
  TRANSFER:  "bg-amber-50 text-amber-600",
};

export default function SowsPage() {
  const t = useTranslations("sows");
  const tStatus = useTranslations("sowStatus");
  const farmId = useAuthStore((s) => s.activeFarmId);
  const router = useRouter();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<SowStatus | "ALL">("ALL");
  const [search, setSearch] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);
  const [editTarget, setEditTarget] = useState<Sow | null>(null);
  const [cullTarget, setCullTarget] = useState<Sow | null>(null);
  const [page, setPage] = useState(1);

  const params = {
    status: statusFilter === "ALL" ? undefined : statusFilter,
    page,
    per_page: 50,
  };

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.sows.list(farmId ?? "", params),
    queryFn: () => sowsApi.list(farmId!, params),
    enabled: !!farmId,
  });

  const sows = data?.items ?? [];
  const meta = data?.meta;

  const filtered = search
    ? sows.filter((s) => s.ear_tag.toLowerCase().includes(search.toLowerCase()))
    : sows;

  if (!farmId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text3">{t("selectFarm")}</p>
      </div>
    );
  }

  return (
    <div className="p-7">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[22px] font-extrabold tracking-tight">{t("title")}</h1>
            <p className="text-xs text-text3 mt-0.5">
              {meta ? t("totalCount", { n: meta.total }) : t("loading")}
            </p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="bg-primary text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-primary/90 transition"
          >
            {t("addSow")}
          </button>
        </div>

        {/* Status tabs + search */}
        <div className="flex items-center justify-between mb-4 gap-4">
          <div className="flex gap-1">
            {STATUS_TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => { setStatusFilter(tab); setPage(1); }}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  statusFilter === tab
                    ? "bg-primary text-white"
                    : "bg-surface border border-border text-text2 hover:bg-border"
                }`}
              >
                {tab === "ALL" ? t("tabAll") : tStatus(tab)}
              </button>
            ))}
          </div>
          <input
            type="text"
            placeholder={t("searchPlaceholder")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="px-3 py-1.5 rounded-lg border border-border bg-surface text-sm text-text1 w-48 outline-none focus:border-primary"
          />
        </div>

        {/* Table */}
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center text-text3 text-sm">{t("loading")}</div>
          ) : isError ? (
            <div className="p-12 text-center text-danger text-sm">{t("loadError")}</div>
          ) : filtered.length === 0 ? (
            <div className="p-12 text-center text-text3 text-sm">
              {search ? t("emptyNoResult", { q: search }) : t("emptyNoSows")}
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-background text-text3 text-xs">
                  <th className="text-left px-4 py-3 font-medium">{t("thEarTag")}</th>
                  <th className="text-left px-4 py-3 font-medium">{t("thStatus")}</th>
                  <th className="text-right px-4 py-3 font-medium">{t("thParity")}</th>
                  <th className="text-left px-4 py-3 font-medium">{t("thBreed")}</th>
                  <th className="text-left px-4 py-3 font-medium">{t("thEntryDate")}</th>
                  <th className="text-left px-4 py-3 font-medium">{t("thNote")}</th>
                  <th className="text-right px-4 py-3 font-medium">{t("thActions")}</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((sow, i) => {
                  const cls = STATUS_CLS[sow.status] ?? "bg-gray-100 text-gray-500";
                  return (
                    <tr
                      key={sow.id}
                      onClick={() => router.push(`/sows/${sow.id}`)}
                      className={`border-b border-border hover:bg-background/50 transition cursor-pointer ${
                        i % 2 === 0 ? "" : "bg-background/20"
                      }`}
                    >
                      <td className="px-4 py-3 font-mono font-bold text-text1">{sow.ear_tag}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold ${cls}`}>
                          {tStatus(sow.status)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-mono">{t("parityUnit", { n: sow.parity })}</td>
                      <td className="px-4 py-3 text-text2">{sow.breed ?? "-"}</td>
                      <td className="px-4 py-3 text-text3 font-mono text-xs">
                        {sow.entry_date.slice(0, 10)}
                      </td>
                      <td className="px-4 py-3 text-text3 text-xs max-w-[160px] truncate">
                        {sow.breed_company ?? "-"}
                      </td>
                      <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => setEditTarget(sow)}
                            title={t("editTooltip")}
                            className="p-1.5 rounded-md text-text3 hover:text-text hover:bg-bg2 transition"
                          >
                            <Pencil size={13} />
                          </button>
                          {sow.status !== "CULLED" && sow.status !== "DEAD" && (
                            <button
                              onClick={() => setCullTarget(sow)}
                              title={t("removalTooltip")}
                              className="p-1.5 rounded-md text-text3 hover:text-red-500 hover:bg-red-50 transition"
                            >
                              <LogOut size={13} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {meta && meta.pages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-4">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 rounded-lg border border-border text-xs disabled:opacity-40"
            >
              {t("prev")}
            </button>
            <span className="text-xs text-text3">{page} / {meta.pages}</span>
            <button
              onClick={() => setPage((p) => Math.min(meta.pages, p + 1))}
              disabled={page === meta.pages}
              className="px-3 py-1.5 rounded-lg border border-border text-xs disabled:opacity-40"
            >
              {t("next")}
            </button>
          </div>
        )}

      {/* Add Sow Modal */}
      {showAddModal && (
        <AddSowModal
          farmId={farmId}
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            setShowAddModal(false);
            queryClient.invalidateQueries({ queryKey: queryKeys.sows.all(farmId) });
          }}
        />
      )}

      {/* Edit Sow Modal */}
      {editTarget && (
        <EditSowModal
          farmId={farmId}
          sow={editTarget}
          onClose={() => setEditTarget(null)}
          onSuccess={() => {
            setEditTarget(null);
            queryClient.invalidateQueries({ queryKey: queryKeys.sows.all(farmId) });
          }}
        />
      )}

      {/* Cull Sow Modal */}
      {cullTarget && (
        <CullSowModal
          farmId={farmId}
          sow={cullTarget}
          onClose={() => setCullTarget(null)}
          onSuccess={() => {
            setCullTarget(null);
            queryClient.invalidateQueries({ queryKey: queryKeys.sows.all(farmId) });
          }}
        />
      )}
    </div>
  );
}

function EditSowModal({
  farmId,
  sow,
  onClose,
  onSuccess,
}: {
  farmId: string;
  sow: Sow;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [form, setForm] = useState<UpdateSowRequest>({
    ear_tag: sow.ear_tag,
    breed: sow.breed ?? "",
    rfid_tag: sow.rfid_tag ?? "",
  });
  const [error, setError] = useState<string | null>(null);
  const t = useTranslations("sows");

  const mutation = useMutation({
    mutationFn: () =>
      sowsApi.update(farmId, sow.id, {
        ear_tag: form.ear_tag,
        breed: form.breed || undefined,
        rfid_tag: form.rfid_tag || undefined,
      }),
    onSuccess,
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === "string" ? msg : t("editFailed"));
    },
  });

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold">{t("editTitle", { tag: sow.ear_tag })}</h2>
          <button onClick={onClose} className="p-1 rounded-md text-text3 hover:text-text hover:bg-bg2 transition">
            <X size={16} />
          </button>
        </div>

        <div className="space-y-3">
          <Field label={t("fEarTag")}>
            <input
              value={form.ear_tag}
              onChange={(e) => setForm((f) => ({ ...f, ear_tag: e.target.value }))}
              className="input"
            />
          </Field>
          <Field label={t("fBreed")}>
            <input
              value={form.breed ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, breed: e.target.value }))}
              placeholder={t("phBreed")}
              className="input"
            />
          </Field>
          <Field label={t("fRfid")}>
            <input
              value={form.rfid_tag ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, rfid_tag: e.target.value }))}
              placeholder={t("phRfid")}
              className="input"
            />
          </Field>
        </div>

        {error && <p className="text-xs text-red-500 mt-3">{error}</p>}

        <div className="flex gap-2 mt-5">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-lg py-2 text-sm">
            {t("cancel")}
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={!form.ear_tag?.trim() || mutation.isPending}
            className="flex-1 bg-primary text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50"
          >
            {mutation.isPending ? t("saving") : t("save")}
          </button>
        </div>
      </div>
    </div>
  );
}

const REMOVAL_TYPE_VALUES: SowCullRequest["removal_type"][] = ["CULLED", "DEAD", "SOLD", "TRANSFER"];
const REASON_CATEGORY_KEYS: { value: NonNullable<SowCullRequest["reason_category"]>; key: string }[] = [
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

function CullSowModal({
  farmId,
  sow,
  onClose,
  onSuccess,
}: {
  farmId: string;
  sow: Sow;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const t = useTranslations("sows");
  const tStatus = useTranslations("sowStatus");
  const [form, setForm] = useState<SowCullRequest>({
    removal_type: "CULLED",
    removal_date: new Date().toISOString().slice(0, 10),
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => sowsApi.cull(farmId, sow.id, form),
    onSuccess,
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === "string" ? msg : t("cullFailed"));
    },
  });

  const isSold = form.removal_type === "SOLD";

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-base font-bold">{t("cullTitle", { tag: sow.ear_tag })}</h2>
          <button onClick={onClose} className="p-1 rounded-md text-text3 hover:text-text hover:bg-bg2 transition">
            <X size={16} />
          </button>
        </div>
        <p className="text-xs text-text3 mb-4">{t("cullNote")}</p>

        <div className="space-y-3">
          <Field label={t("fRemovalType")}>
            <div className="grid grid-cols-4 gap-1.5">
              {REMOVAL_TYPE_VALUES.map((rt) => (
                <button
                  key={rt}
                  type="button"
                  onClick={() => setForm((f) => ({ ...f, removal_type: rt }))}
                  className={`py-2 rounded-lg text-xs font-semibold border transition ${
                    form.removal_type === rt
                      ? "bg-primary text-white border-primary"
                      : "bg-white text-text2 border-border hover:border-text3/50"
                  }`}
                >
                  {tStatus(rt)}
                </button>
              ))}
            </div>
          </Field>
          <Field label={t("fRemovalDate")}>
            <input
              type="date"
              value={form.removal_date}
              onChange={(e) => setForm((f) => ({ ...f, removal_date: e.target.value }))}
              className="input"
            />
          </Field>
          <Field label={t("fReason")}>
            <select
              value={form.reason_category ?? ""}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  reason_category: (e.target.value || undefined) as SowCullRequest["reason_category"],
                }))
              }
              className="input"
            >
              <option value="">{t("select")}</option>
              {REASON_CATEGORY_KEYS.map((r) => (
                <option key={r.value} value={r.value}>{t(r.key)}</option>
              ))}
            </select>
          </Field>
          {isSold && (
            <div className="grid grid-cols-2 gap-3">
              <Field label={t("fWeight")}>
                <input
                  type="number"
                  min={0}
                  value={form.body_weight_kg ?? ""}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, body_weight_kg: e.target.value ? Number(e.target.value) : undefined }))
                  }
                  className="input"
                />
              </Field>
              <Field label={t("fSalePrice")}>
                <input
                  type="number"
                  min={0}
                  value={form.sale_price ?? ""}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      sale_price: e.target.value ? Number(e.target.value) : undefined,
                      sale_currency: e.target.value ? "KRW" : undefined,
                    }))
                  }
                  className="input"
                />
              </Field>
            </div>
          )}
          <Field label={t("fNote")}>
            <input
              value={form.notes ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value || undefined }))}
              placeholder={t("phNote")}
              className="input"
            />
          </Field>
        </div>

        {error && <p className="text-xs text-red-500 mt-3">{error}</p>}

        <div className="flex gap-2 mt-5">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-lg py-2 text-sm">
            {t("cancel")}
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={!form.removal_date || mutation.isPending}
            className="flex-1 bg-red-500 hover:bg-red-600 text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50 transition"
          >
            {mutation.isPending ? t("culling") : t("cullConfirm")}
          </button>
        </div>
      </div>
    </div>
  );
}

function AddSowModal({
  farmId,
  onClose,
  onSuccess,
}: {
  farmId: string;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const t = useTranslations("sows");
  const [form, setForm] = useState<CreateSowRequest>({
    ear_tag: "",
    entry_date: new Date().toISOString().slice(0, 10),
    entry_type: "GILT",
    parity: 0,
    breed: "",
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => sowsApi.create(farmId, form),
    onSuccess,
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === "string" ? msg : t("regFailed"));
    },
  });

  const set = (k: keyof CreateSowRequest, v: string | number) =>
    setForm((f) => ({ ...f, [k]: v }));

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl">
        <h2 className="text-base font-bold mb-4">{t("regTitle")}</h2>

        <div className="space-y-3">
          <Field label={t("fEarTag")}>
            <input
              value={form.ear_tag}
              onChange={(e) => set("ear_tag", e.target.value)}
              placeholder={t("phEarTag")}
              className="input"
            />
          </Field>
          <Field label={t("fEntryDate")}>
            <input
              type="date"
              value={form.entry_date}
              onChange={(e) => set("entry_date", e.target.value)}
              className="input"
            />
          </Field>
          <Field label={t("fEntryType")}>
            <select
              value={form.entry_type}
              onChange={(e) => set("entry_type", e.target.value as SowEntryType)}
              className="input"
            >
              <option value="GILT">{t("entryGilt")}</option>
              <option value="PURCHASE">{t("entryPurchase")}</option>
              <option value="TRANSFER">{t("entryTransfer")}</option>
              <option value="BORN">{t("entryBorn")}</option>
            </select>
          </Field>
          <Field label={t("fParity")}>
            <input
              type="number"
              value={form.parity}
              min={0}
              onChange={(e) => set("parity", Number(e.target.value))}
              className="input"
            />
          </Field>
          <Field label={t("fBreed")}>
            <input
              value={form.breed ?? ""}
              onChange={(e) => set("breed", e.target.value)}
              placeholder={t("phBreed")}
              className="input"
            />
          </Field>
        </div>

        {error && <p className="text-xs text-red-500 mt-3">{error}</p>}

        <div className="flex gap-2 mt-5">
          <button
            onClick={onClose}
            className="flex-1 border border-gray-200 rounded-lg py-2 text-sm"
          >
            {t("cancel")}
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={!form.ear_tag || mutation.isPending}
            className="flex-1 bg-primary text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50"
          >
            {mutation.isPending ? t("regging") : t("reg")}
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

"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, X } from "lucide-react";
import { useAuthStore } from "@/store/auth.store";
import {
  boarsApi,
  type Boar,
  type CreateBoarRequest,
  type UpdateBoarRequest,
} from "@/lib/api/endpoints/boars";

const STATUS_LABEL: Record<string, string> = {
  ACTIVE: "활성",
  CULLED: "도태",
  DEAD: "폐사",
  TRANSFERRED: "전출",
};

const STATUS_CLASS: Record<string, string> = {
  ACTIVE:      "bg-green-50 text-green-700 border-green-100",
  CULLED:      "bg-red-50 text-red-500 border-red-100",
  DEAD:        "bg-gray-100 text-gray-400 border-gray-200",
  TRANSFERRED: "bg-amber-50 text-amber-600 border-amber-100",
};

const BREEDS = ["Duroc", "Landrace", "Yorkshire", "Berkshire", "Pietrain", "Hampshire"];
const SEMEN_QUALITY = [
  { value: "EXCELLENT", label: "최우수" },
  { value: "GOOD",      label: "우수" },
  { value: "FAIR",      label: "보통" },
  { value: "POOR",      label: "불량" },
];
const ENTRY_TYPES = [
  { value: "PURCHASE", label: "구입" },
  { value: "BORN",     label: "자가생산" },
  { value: "TRANSFER", label: "전입" },
];

const EMPTY_FORM: CreateBoarRequest = {
  ear_tag: "",
  breed: "",
  breed_company: "",
  entry_date: "",
  entry_type: "PURCHASE",
  semen_quality: "",
};

export default function BoarsPage() {
  const activeFarmId = useAuthStore((s) => s.activeFarmId);
  const farmId = activeFarmId ?? "";
  const queryClient = useQueryClient();

  const [statusFilter, setStatusFilter] = useState<string>("");
  const [modal, setModal] = useState<"create" | "edit" | null>(null);
  const [editTarget, setEditTarget] = useState<Boar | null>(null);
  const [form, setForm] = useState<CreateBoarRequest>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);

  const { data: boars = [], isLoading, error } = useQuery({
    queryKey: ["boars", farmId, statusFilter],
    queryFn: () => boarsApi.list(farmId, statusFilter || undefined),
    enabled: !!farmId,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["boars", farmId] });

  const closeModal = () => {
    setModal(null);
    setEditTarget(null);
    setForm(EMPTY_FORM);
    setFormError(null);
  };

  const createMutation = useMutation({
    mutationFn: (body: CreateBoarRequest) => boarsApi.create(farmId, body),
    onSuccess: () => { invalidate(); closeModal(); },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFormError(typeof detail === "string" ? detail : "등록에 실패했습니다");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdateBoarRequest }) =>
      boarsApi.update(farmId, id, body),
    onSuccess: () => { invalidate(); closeModal(); },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFormError(typeof detail === "string" ? detail : "수정에 실패했습니다");
    },
  });

  const openCreate = () => {
    setForm({ ...EMPTY_FORM, entry_date: new Date().toISOString().slice(0, 10) });
    setModal("create");
  };

  const openEdit = (boar: Boar) => {
    setEditTarget(boar);
    setForm({
      ear_tag: boar.ear_tag,
      breed: boar.breed ?? "",
      breed_company: boar.breed_company ?? "",
      entry_date: boar.entry_date.slice(0, 10),
      entry_type: boar.entry_type ?? "PURCHASE",
      semen_quality: boar.semen_quality ?? "",
    });
    setModal("edit");
  };

  const submit = () => {
    setFormError(null);
    if (!form.ear_tag.trim()) { setFormError("이표번호를 입력하세요"); return; }
    if (modal === "create") {
      if (!form.entry_date) { setFormError("도입일을 선택하세요"); return; }
      createMutation.mutate({
        ...form,
        breed: form.breed || undefined,
        breed_company: form.breed_company || undefined,
        semen_quality: form.semen_quality || undefined,
      });
    } else if (modal === "edit" && editTarget) {
      updateMutation.mutate({
        id: editTarget.id,
        body: {
          ear_tag: form.ear_tag,
          breed: form.breed || undefined,
          breed_company: form.breed_company || undefined,
          semen_quality: form.semen_quality || undefined,
        },
      });
    }
  };

  const changeStatus = (boar: Boar, status: Boar["status"]) => {
    updateMutation.mutate({ id: boar.id, body: { status } });
  };

  const activeCount = boars.filter((b) => b.status === "ACTIVE").length;
  const pending = createMutation.isPending || updateMutation.isPending;

  return (
    <main className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text">웅돈 관리</h1>
          <p className="text-sm text-text3 mt-0.5">활성 웅돈 {activeCount}두</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-sm border border-border rounded-lg px-3 py-1.5 bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary/30"
          >
            <option value="">전체 상태</option>
            <option value="ACTIVE">활성</option>
            <option value="CULLED">도태</option>
            <option value="DEAD">폐사</option>
            <option value="TRANSFERRED">전출</option>
          </select>
          <button
            onClick={openCreate}
            className="flex items-center gap-1.5 bg-primary text-white text-sm font-semibold px-3.5 py-1.5 rounded-lg hover:bg-blue-700 transition"
          >
            <Plus size={15} />
            웅돈 등록
          </button>
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="text-sm text-text3 py-12 text-center">로딩 중...</div>
      ) : error ? (
        <div className="text-sm text-danger py-12 text-center">데이터를 불러오지 못했습니다</div>
      ) : boars.length === 0 ? (
        <div className="border border-dashed border-border rounded-xl py-14 text-center">
          <p className="text-sm text-text3 mb-3">
            {statusFilter ? "해당 상태의 웅돈이 없습니다" : "등록된 웅돈이 없습니다"}
          </p>
          {!statusFilter && (
            <button onClick={openCreate} className="text-sm font-semibold text-primary hover:underline">
              첫 웅돈 등록하기
            </button>
          )}
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-bg2">
                <th className="text-left px-4 py-3 text-text3 font-medium">이표번호</th>
                <th className="text-left px-4 py-3 text-text3 font-medium">품종</th>
                <th className="text-left px-4 py-3 text-text3 font-medium">도입일</th>
                <th className="text-left px-4 py-3 text-text3 font-medium">정액 품질</th>
                <th className="text-left px-4 py-3 text-text3 font-medium">상태</th>
                <th className="text-right px-4 py-3 text-text3 font-medium">관리</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {boars.map((boar: Boar) => (
                <tr key={boar.id} className="hover:bg-bg2/50 transition-colors">
                  <td className="px-4 py-3 font-mono font-semibold text-text">{boar.ear_tag}</td>
                  <td className="px-4 py-3 text-text1">{boar.breed ?? "—"}</td>
                  <td className="px-4 py-3 text-text2">{boar.entry_date.slice(0, 10)}</td>
                  <td className="px-4 py-3 text-text2">
                    {SEMEN_QUALITY.find((q) => q.value === boar.semen_quality)?.label ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${STATUS_CLASS[boar.status] ?? "bg-gray-50 text-gray-500"}`}>
                      {STATUS_LABEL[boar.status] ?? boar.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => openEdit(boar)}
                        title="수정"
                        className="p-1.5 rounded-md text-text3 hover:text-text hover:bg-bg2 transition"
                      >
                        <Pencil size={13} />
                      </button>
                      {boar.status === "ACTIVE" && (
                        <select
                          value=""
                          onChange={(e) => {
                            if (e.target.value) changeStatus(boar, e.target.value as Boar["status"]);
                          }}
                          className="text-xs border border-border rounded-md px-1.5 py-1 bg-surface text-text3 focus:outline-none"
                        >
                          <option value="">상태 변경</option>
                          <option value="CULLED">도태</option>
                          <option value="DEAD">폐사</option>
                          <option value="TRANSFERRED">전출</option>
                        </select>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create / Edit modal */}
      {modal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4" onClick={closeModal}>
          <div
            className="w-full max-w-md bg-surface rounded-2xl border border-border shadow-xl p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-base font-bold text-text">
                {modal === "create" ? "웅돈 등록" : `웅돈 수정 — ${editTarget?.ear_tag}`}
              </h2>
              <button onClick={closeModal} className="p-1 rounded-md text-text3 hover:text-text hover:bg-bg2 transition">
                <X size={16} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-text3 mb-1.5">이표번호 *</label>
                <input
                  value={form.ear_tag}
                  onChange={(e) => setForm((f) => ({ ...f, ear_tag: e.target.value }))}
                  placeholder="예: B-001"
                  className="w-full h-10 px-3 text-sm border border-border rounded-lg bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-text3 mb-1.5">품종</label>
                  <select
                    value={form.breed}
                    onChange={(e) => setForm((f) => ({ ...f, breed: e.target.value }))}
                    className="w-full h-10 px-3 text-sm border border-border rounded-lg bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary/30"
                  >
                    <option value="">선택</option>
                    {BREEDS.map((b) => <option key={b} value={b}>{b}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-text3 mb-1.5">종돈장</label>
                  <input
                    value={form.breed_company}
                    onChange={(e) => setForm((f) => ({ ...f, breed_company: e.target.value }))}
                    placeholder="예: PIC"
                    className="w-full h-10 px-3 text-sm border border-border rounded-lg bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary/30"
                  />
                </div>
              </div>

              {modal === "create" && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-text3 mb-1.5">도입일 *</label>
                    <input
                      type="date"
                      value={form.entry_date}
                      onChange={(e) => setForm((f) => ({ ...f, entry_date: e.target.value }))}
                      className="w-full h-10 px-3 text-sm border border-border rounded-lg bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary/30"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-text3 mb-1.5">도입 구분</label>
                    <select
                      value={form.entry_type}
                      onChange={(e) => setForm((f) => ({ ...f, entry_type: e.target.value }))}
                      className="w-full h-10 px-3 text-sm border border-border rounded-lg bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary/30"
                    >
                      {ENTRY_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                    </select>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-text3 mb-1.5">정액 품질</label>
                <select
                  value={form.semen_quality}
                  onChange={(e) => setForm((f) => ({ ...f, semen_quality: e.target.value }))}
                  className="w-full h-10 px-3 text-sm border border-border rounded-lg bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary/30"
                >
                  <option value="">선택</option>
                  {SEMEN_QUALITY.map((q) => <option key={q.value} value={q.value}>{q.label}</option>)}
                </select>
              </div>

              {formError && (
                <div className="bg-red-50 border border-red-200 rounded-lg px-3.5 py-2.5 text-sm text-red-600">
                  {formError}
                </div>
              )}

              <div className="flex gap-2.5 pt-1">
                <button
                  onClick={closeModal}
                  className="flex-1 h-10 border border-border text-text2 rounded-lg text-sm font-medium hover:bg-bg2 transition"
                >
                  취소
                </button>
                <button
                  onClick={submit}
                  disabled={pending}
                  className="flex-1 h-10 bg-primary text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition"
                >
                  {pending ? "저장 중…" : modal === "create" ? "등록" : "저장"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

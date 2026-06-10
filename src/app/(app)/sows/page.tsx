"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
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
const STATUS_TABS: { label: string; value: SowStatus | "ALL" }[] = [
  { label: "전체",   value: "ALL" },
  { label: "후보돈", value: "GILT" },
  { label: "공태",   value: "OPEN" },
  { label: "임신",   value: "PREGNANT" },
  { label: "포유",   value: "LACTATING" },
  { label: "사고",   value: "ACCIDENT" },
  { label: "도태",   value: "CULLED" },
];

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

export default function SowsPage() {
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
        <p className="text-text3">농장을 선택해주세요.</p>
      </div>
    );
  }

  return (
    <div className="p-7">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[22px] font-extrabold tracking-tight">모돈 관리</h1>
            <p className="text-xs text-text3 mt-0.5">
              {meta ? `총 ${meta.total}두` : "불러오는 중..."}
            </p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="bg-primary text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-primary/90 transition"
          >
            + 모돈 등록
          </button>
        </div>

        {/* Status tabs + search */}
        <div className="flex items-center justify-between mb-4 gap-4">
          <div className="flex gap-1">
            {STATUS_TABS.map((tab) => (
              <button
                key={tab.value}
                onClick={() => { setStatusFilter(tab.value); setPage(1); }}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  statusFilter === tab.value
                    ? "bg-primary text-white"
                    : "bg-surface border border-border text-text2 hover:bg-border"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <input
            type="text"
            placeholder="귀표 번호 검색..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="px-3 py-1.5 rounded-lg border border-border bg-surface text-sm text-text1 w-48 outline-none focus:border-primary"
          />
        </div>

        {/* Table */}
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center text-text3 text-sm">불러오는 중...</div>
          ) : isError ? (
            <div className="p-12 text-center text-danger text-sm">데이터를 불러오지 못했습니다.</div>
          ) : filtered.length === 0 ? (
            <div className="p-12 text-center text-text3 text-sm">
              {search ? `"${search}" 검색 결과 없음` : "등록된 모돈이 없습니다."}
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-background text-text3 text-xs">
                  <th className="text-left px-4 py-3 font-medium">귀표</th>
                  <th className="text-left px-4 py-3 font-medium">상태</th>
                  <th className="text-right px-4 py-3 font-medium">산차</th>
                  <th className="text-left px-4 py-3 font-medium">품종</th>
                  <th className="text-left px-4 py-3 font-medium">입식일</th>
                  <th className="text-left px-4 py-3 font-medium">비고</th>
                  <th className="text-right px-4 py-3 font-medium">관리</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((sow, i) => {
                  const badge = STATUS_BADGE[sow.status] ?? { label: sow.status, cls: "bg-gray-100 text-gray-500" };
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
                        <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold ${badge.cls}`}>
                          {badge.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-mono">{sow.parity}산</td>
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
                            title="수정"
                            className="p-1.5 rounded-md text-text3 hover:text-text hover:bg-bg2 transition"
                          >
                            <Pencil size={13} />
                          </button>
                          {sow.status !== "CULLED" && sow.status !== "DEAD" && (
                            <button
                              onClick={() => setCullTarget(sow)}
                              title="도폐사/판매 처리"
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
              이전
            </button>
            <span className="text-xs text-text3">{page} / {meta.pages}</span>
            <button
              onClick={() => setPage((p) => Math.min(meta.pages, p + 1))}
              disabled={page === meta.pages}
              className="px-3 py-1.5 rounded-lg border border-border text-xs disabled:opacity-40"
            >
              다음
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
      setError(typeof msg === "string" ? msg : "수정 실패");
    },
  });

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold">모돈 수정 — {sow.ear_tag}</h2>
          <button onClick={onClose} className="p-1 rounded-md text-text3 hover:text-text hover:bg-bg2 transition">
            <X size={16} />
          </button>
        </div>

        <div className="space-y-3">
          <Field label="귀표 번호 *">
            <input
              value={form.ear_tag}
              onChange={(e) => setForm((f) => ({ ...f, ear_tag: e.target.value }))}
              className="input"
            />
          </Field>
          <Field label="품종">
            <input
              value={form.breed ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, breed: e.target.value }))}
              placeholder="예: Yorkshire, Landrace"
              className="input"
            />
          </Field>
          <Field label="RFID 태그">
            <input
              value={form.rfid_tag ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, rfid_tag: e.target.value }))}
              placeholder="RFID 번호"
              className="input"
            />
          </Field>
        </div>

        {error && <p className="text-xs text-red-500 mt-3">{error}</p>}

        <div className="flex gap-2 mt-5">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-lg py-2 text-sm">
            취소
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={!form.ear_tag?.trim() || mutation.isPending}
            className="flex-1 bg-primary text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50"
          >
            {mutation.isPending ? "저장 중..." : "저장"}
          </button>
        </div>
      </div>
    </div>
  );
}

const REMOVAL_TYPES: { value: SowCullRequest["removal_type"]; label: string }[] = [
  { value: "CULLED",   label: "도태" },
  { value: "DEAD",     label: "폐사" },
  { value: "SOLD",     label: "판매" },
  { value: "TRANSFER", label: "전출" },
];

const REASON_CATEGORIES: { value: NonNullable<SowCullRequest["reason_category"]>; label: string }[] = [
  { value: "REPRODUCTIVE", label: "번식 장애" },
  { value: "LAMENESS",     label: "지제 불량" },
  { value: "DISEASE",      label: "질병" },
  { value: "AGE",          label: "노령" },
  { value: "PERFORMANCE",  label: "성적 불량" },
  { value: "INJURY",       label: "부상" },
  { value: "BEHAVIOR",     label: "행동 문제" },
  { value: "UNKNOWN",      label: "원인 불명" },
  { value: "OTHER",        label: "기타" },
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
      setError(typeof msg === "string" ? msg : "처리 실패");
    },
  });

  const isSold = form.removal_type === "SOLD";

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-base font-bold">도폐사·판매 처리 — {sow.ear_tag}</h2>
          <button onClick={onClose} className="p-1 rounded-md text-text3 hover:text-text hover:bg-bg2 transition">
            <X size={16} />
          </button>
        </div>
        <p className="text-xs text-text3 mb-4">처리 후 모돈 목록에서 제외되며 removals 이력에 기록됩니다</p>

        <div className="space-y-3">
          <Field label="처리 구분 *">
            <div className="grid grid-cols-4 gap-1.5">
              {REMOVAL_TYPES.map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => setForm((f) => ({ ...f, removal_type: t.value }))}
                  className={`py-2 rounded-lg text-xs font-semibold border transition ${
                    form.removal_type === t.value
                      ? "bg-primary text-white border-primary"
                      : "bg-white text-text2 border-border hover:border-text3/50"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </Field>
          <Field label="처리일 *">
            <input
              type="date"
              value={form.removal_date}
              onChange={(e) => setForm((f) => ({ ...f, removal_date: e.target.value }))}
              className="input"
            />
          </Field>
          <Field label="사유">
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
              <option value="">선택</option>
              {REASON_CATEGORIES.map((r) => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </Field>
          {isSold && (
            <div className="grid grid-cols-2 gap-3">
              <Field label="체중 (kg)">
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
              <Field label="판매가">
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
          <Field label="비고">
            <input
              value={form.notes ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value || undefined }))}
              placeholder="상세 사유 등"
              className="input"
            />
          </Field>
        </div>

        {error && <p className="text-xs text-red-500 mt-3">{error}</p>}

        <div className="flex gap-2 mt-5">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-lg py-2 text-sm">
            취소
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={!form.removal_date || mutation.isPending}
            className="flex-1 bg-red-500 hover:bg-red-600 text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50 transition"
          >
            {mutation.isPending ? "처리 중..." : "처리 확정"}
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
      setError(msg ?? "등록 실패");
    },
  });

  const set = (k: keyof CreateSowRequest, v: string | number) =>
    setForm((f) => ({ ...f, [k]: v }));

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl">
        <h2 className="text-base font-bold mb-4">모돈 등록</h2>

        <div className="space-y-3">
          <Field label="귀표 번호 *">
            <input
              value={form.ear_tag}
              onChange={(e) => set("ear_tag", e.target.value)}
              placeholder="예: A-042"
              className="input"
            />
          </Field>
          <Field label="입식일 *">
            <input
              type="date"
              value={form.entry_date}
              onChange={(e) => set("entry_date", e.target.value)}
              className="input"
            />
          </Field>
          <Field label="입식 구분 *">
            <select
              value={form.entry_type}
              onChange={(e) => set("entry_type", e.target.value as SowEntryType)}
              className="input"
            >
              <option value="GILT">육성돈 (Gilt)</option>
              <option value="PURCHASE">구매</option>
              <option value="TRANSFER">전입</option>
              <option value="BORN">자가생산</option>
            </select>
          </Field>
          <Field label="산차 (초산 전=0)">
            <input
              type="number"
              value={form.parity}
              min={0}
              onChange={(e) => set("parity", Number(e.target.value))}
              className="input"
            />
          </Field>
          <Field label="품종">
            <input
              value={form.breed ?? ""}
              onChange={(e) => set("breed", e.target.value)}
              placeholder="예: Yorkshire, Landrace"
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
            취소
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={!form.ear_tag || mutation.isPending}
            className="flex-1 bg-primary text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50"
          >
            {mutation.isPending ? "등록 중..." : "등록"}
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

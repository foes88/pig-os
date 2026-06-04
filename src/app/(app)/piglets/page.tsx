"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { pigletsApi } from "@/lib/api/endpoints/piglets";
import { useAuthStore } from "@/store/auth.store";
import type { CreatePigletGroupRequest, PigletGroupTransferOutRequest } from "@/types/api.types";

const TRANSFER_TYPE_LABELS: Record<string, string> = {
  FINISHER_TRANSFER: "비육사 전출",
  SOLD: "판매",
  CULLED: "도태",
};

export default function PigletsPage() {
  const farmId = useAuthStore((s) => s.activeFarmId);
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
        <p className="text-text3">농장을 선택해주세요.</p>
      </div>
    );
  }

  return (
    <div className="p-7">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[22px] font-extrabold tracking-tight">자돈 관리</h1>
            <p className="text-xs text-text3 mt-0.5">이유 후 자돈 그룹 관리</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setActiveOnly((v) => !v)}
              className={`px-3 py-2 rounded-lg text-xs font-medium border transition ${
                activeOnly ? "bg-primary text-white" : "bg-surface border-border text-text2"
              }`}
            >
              {activeOnly ? "사육중만" : "전체"}
            </button>
            <button
              onClick={() => setShowForm(true)}
              className="bg-primary text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-primary/90 transition"
            >
              + 그룹 시작
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-20 text-text3 text-sm">불러오는 중...</div>
        ) : groups.length === 0 ? (
          <div className="text-center py-20 text-text3 text-sm">
            {activeOnly ? "사육 중인 자돈 그룹이 없습니다." : "등록된 그룹이 없습니다."}
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
                          isActive ? "bg-blue-50 text-blue-600" : "bg-slate-100 text-slate-500"
                        }`}>
                          {isActive ? "사육중" : (TRANSFER_TYPE_LABELS[g.transfer_type ?? ""] ?? "전출완료")}
                        </span>
                      </div>
                      <div className="text-xs text-text3 mt-0.5">
                        이유일 {g.weaning_date} · 입식 {g.head_count_in}두
                        {g.avg_entry_weight_kg && ` · 평균 ${g.avg_entry_weight_kg}kg`}
                      </div>
                    </div>
                    <div className="flex gap-5 text-sm">
                      <div>
                        <div className="text-[10px] text-text3">생존</div>
                        <div className="font-medium font-mono">{surviving}두</div>
                      </div>
                      <div>
                        <div className="text-[10px] text-text3">폐사율</div>
                        <div className={`font-medium font-mono ${Number(mortalityRate) > 5 ? "text-danger" : "text-success"}`}>
                          {mortalityRate}%
                        </div>
                      </div>
                      {!isActive && g.transfer_date && (
                        <div>
                          <div className="text-[10px] text-text3">전출일</div>
                          <div className="font-medium">{g.transfer_date}</div>
                        </div>
                      )}
                    </div>
                  </div>
                  {isActive && (
                    <button
                      onClick={() => setTransferId(g.id)}
                      className="bg-blue-500 text-white px-4 py-2 rounded-lg text-xs font-semibold hover:bg-blue-500/90 transition"
                    >
                      전출/판매
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
  const [form, setForm] = useState<CreatePigletGroupRequest>({
    group_code: "",
    weaning_date: new Date().toISOString().slice(0, 10),
    head_count_in: 0,
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => pigletsApi.create(farmId, form),
    onSuccess,
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "등록 실패");
    },
  });

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl">
        <h2 className="text-base font-bold mb-4">자돈 그룹 시작</h2>
        <div className="space-y-3">
          <Field label="그룹 코드 *">
            <input value={form.group_code} onChange={(e) => setForm((f) => ({ ...f, group_code: e.target.value }))}
              placeholder="예: PG-2026-001" className="input" />
          </Field>
          <Field label="배치명">
            <input value={form.batch_name ?? ""} onChange={(e) => setForm((f) => ({ ...f, batch_name: e.target.value }))}
              placeholder="예: 6월 1차 이유" className="input" />
          </Field>
          <Field label="이유일 *">
            <input type="date" value={form.weaning_date} onChange={(e) => setForm((f) => ({ ...f, weaning_date: e.target.value }))} className="input" />
          </Field>
          <Field label="두수 *">
            <input type="number" min={1} value={form.head_count_in || ""} onChange={(e) => setForm((f) => ({ ...f, head_count_in: Number(e.target.value) }))} className="input" />
          </Field>
          <Field label="평균 이유 체중 (kg)">
            <input type="number" step="0.1" min={0} value={form.avg_entry_weight_kg ?? ""} onChange={(e) => setForm((f) => ({ ...f, avg_entry_weight_kg: Number(e.target.value) || undefined }))} placeholder="예: 7.5" className="input" />
          </Field>
        </div>
        {error && <p className="text-xs text-red-500 mt-3">{error}</p>}
        <div className="flex gap-2 mt-5">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-lg py-2 text-sm">취소</button>
          <button onClick={() => mutation.mutate()} disabled={!form.group_code || !form.head_count_in || mutation.isPending}
            className="flex-1 bg-primary text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50">
            {mutation.isPending ? "등록 중..." : "그룹 시작"}
          </button>
        </div>
      </div>
    </div>
  );
}

function TransferModal({ farmId, groupId, onClose, onSuccess }: { farmId: string; groupId: string; onClose: () => void; onSuccess: () => void }) {
  const [form, setForm] = useState<PigletGroupTransferOutRequest>({
    transfer_date: new Date().toISOString().slice(0, 10),
    transfer_type: "FINISHER_TRANSFER",
    head_count_out: 0,
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => pigletsApi.transferOut(farmId, groupId, form),
    onSuccess,
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "처리 실패");
    },
  });

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl">
        <h2 className="text-base font-bold mb-4">자돈 전출/판매</h2>
        <div className="space-y-3">
          <Field label="처리 유형 *">
            <select value={form.transfer_type} onChange={(e) => setForm((f) => ({ ...f, transfer_type: e.target.value as PigletGroupTransferOutRequest["transfer_type"] }))} className="input">
              <option value="FINISHER_TRANSFER">비육사 전출</option>
              <option value="SOLD">외부 판매</option>
              <option value="CULLED">도태</option>
            </select>
          </Field>
          <Field label="처리일 *">
            <input type="date" value={form.transfer_date} onChange={(e) => setForm((f) => ({ ...f, transfer_date: e.target.value }))} className="input" />
          </Field>
          <Field label="두수 *">
            <input type="number" min={1} value={form.head_count_out || ""} onChange={(e) => setForm((f) => ({ ...f, head_count_out: Number(e.target.value) }))} className="input" />
          </Field>
          <Field label="평균 체중 (kg)">
            <input type="number" step="0.1" min={0} value={form.avg_exit_weight_kg ?? ""} onChange={(e) => setForm((f) => ({ ...f, avg_exit_weight_kg: Number(e.target.value) || undefined }))} placeholder="예: 28.0" className="input" />
          </Field>
        </div>
        {error && <p className="text-xs text-red-500 mt-3">{error}</p>}
        <div className="flex gap-2 mt-5">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-lg py-2 text-sm">취소</button>
          <button onClick={() => mutation.mutate()} disabled={!form.head_count_out || mutation.isPending}
            className="flex-1 bg-blue-500 text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50">
            {mutation.isPending ? "처리 중..." : "전출 완료"}
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

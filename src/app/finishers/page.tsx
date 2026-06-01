"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Sidebar } from "@/components/Sidebar";
import { finishersApi } from "@/lib/api/endpoints/finishers";
import { useAuthStore } from "@/store/auth.store";
import type { CreateFinisherGroupRequest, FinisherGroupShipRequest } from "@/types/api.types";

export default function FinishersPage() {
  const farmId = useAuthStore((s) => s.activeFarmId);
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [shippingId, setShippingId] = useState<string | null>(null);
  const [activeOnly, setActiveOnly] = useState(true);

  const { data: groups = [], isLoading } = useQuery({
    queryKey: ["finishers", farmId, activeOnly],
    queryFn: () => finishersApi.list(farmId!, activeOnly),
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
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="ml-[220px] p-7">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[22px] font-extrabold tracking-tight">비육돈 관리</h1>
            <p className="text-xs text-text3 mt-0.5">그룹 단위 입식·출하 관리</p>
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
              + 그룹 입식
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-20 text-text3 text-sm">불러오는 중...</div>
        ) : groups.length === 0 ? (
          <div className="text-center py-20 text-text3 text-sm">
            {activeOnly ? "사육 중인 비육돈 그룹이 없습니다." : "등록된 그룹이 없습니다."}
          </div>
        ) : (
          <div className="grid gap-3">
            {groups.map((g) => {
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
                          {isActive ? "사육중" : "출하완료"}
                        </span>
                      </div>
                      <div className="text-xs text-text3 mt-0.5">
                        입식 {g.start_date} · {g.head_count_in}두
                        {g.avg_entry_weight_kg && ` · 평균 ${g.avg_entry_weight_kg}kg`}
                      </div>
                    </div>
                    <div className="flex gap-6 text-sm">
                      {g.end_date && (
                        <>
                          <div>
                            <div className="text-[10px] text-text3">출하일</div>
                            <div className="font-medium">{g.end_date}</div>
                          </div>
                          <div>
                            <div className="text-[10px] text-text3">출하두수</div>
                            <div className="font-medium">{g.head_count_out}두</div>
                          </div>
                          {g.avg_exit_weight_kg && (
                            <div>
                              <div className="text-[10px] text-text3">출하체중</div>
                              <div className="font-medium">{g.avg_exit_weight_kg}kg</div>
                            </div>
                          )}
                          {mortality != null && (
                            <div>
                              <div className="text-[10px] text-text3">폐사</div>
                              <div className={`font-medium ${mortality > 0 ? "text-danger" : "text-success"}`}>
                                {mortality}두
                              </div>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                  {isActive && (
                    <button
                      onClick={() => setShippingId(g.id)}
                      className="bg-amber-500 text-white px-4 py-2 rounded-lg text-xs font-semibold hover:bg-amber-500/90 transition"
                    >
                      출하 처리
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </main>

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
    </div>
  );
}

function CreateGroupModal({ farmId, onClose, onSuccess }: { farmId: string; onClose: () => void; onSuccess: () => void }) {
  const [form, setForm] = useState<CreateFinisherGroupRequest>({
    group_code: "",
    start_date: new Date().toISOString().slice(0, 10),
    head_count_in: 0,
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => finishersApi.create(farmId, form),
    onSuccess,
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "등록 실패");
    },
  });

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl">
        <h2 className="text-base font-bold mb-4">비육돈 그룹 입식</h2>
        <div className="space-y-3">
          <Field label="그룹 코드 *">
            <input value={form.group_code} onChange={(e) => setForm((f) => ({ ...f, group_code: e.target.value }))}
              placeholder="예: FG-2026-001" className="input" />
          </Field>
          <Field label="배치명">
            <input value={form.batch_name ?? ""} onChange={(e) => setForm((f) => ({ ...f, batch_name: e.target.value }))}
              placeholder="예: 6월 1차" className="input" />
          </Field>
          <Field label="입식일 *">
            <input type="date" value={form.start_date} onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))} className="input" />
          </Field>
          <Field label="입식 두수 *">
            <input type="number" min={1} value={form.head_count_in || ""} onChange={(e) => setForm((f) => ({ ...f, head_count_in: Number(e.target.value) }))} className="input" />
          </Field>
          <Field label="평균 입식 체중 (kg)">
            <input type="number" step="0.1" min={0} value={form.avg_entry_weight_kg ?? ""} onChange={(e) => setForm((f) => ({ ...f, avg_entry_weight_kg: Number(e.target.value) || undefined }))} placeholder="예: 28.5" className="input" />
          </Field>
        </div>
        {error && <p className="text-xs text-red-500 mt-3">{error}</p>}
        <div className="flex gap-2 mt-5">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-lg py-2 text-sm">취소</button>
          <button onClick={() => mutation.mutate()} disabled={!form.group_code || !form.head_count_in || mutation.isPending}
            className="flex-1 bg-primary text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50">
            {mutation.isPending ? "등록 중..." : "등록"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ShipModal({ farmId, groupId, onClose, onSuccess }: { farmId: string; groupId: string; onClose: () => void; onSuccess: () => void }) {
  const [form, setForm] = useState<FinisherGroupShipRequest>({
    end_date: new Date().toISOString().slice(0, 10),
    head_count_out: 0,
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => finishersApi.ship(farmId, groupId, form),
    onSuccess,
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "출하 처리 실패");
    },
  });

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl">
        <h2 className="text-base font-bold mb-4">출하 처리</h2>
        <div className="space-y-3">
          <Field label="출하일 *">
            <input type="date" value={form.end_date} onChange={(e) => setForm((f) => ({ ...f, end_date: e.target.value }))} className="input" />
          </Field>
          <Field label="출하 두수 *">
            <input type="number" min={1} value={form.head_count_out || ""} onChange={(e) => setForm((f) => ({ ...f, head_count_out: Number(e.target.value) }))} className="input" />
          </Field>
          <Field label="평균 출하 체중 (kg)">
            <input type="number" step="0.1" min={0} value={form.avg_exit_weight_kg ?? ""} onChange={(e) => setForm((f) => ({ ...f, avg_exit_weight_kg: Number(e.target.value) || undefined }))} placeholder="예: 115.0" className="input" />
          </Field>
        </div>
        {error && <p className="text-xs text-red-500 mt-3">{error}</p>}
        <div className="flex gap-2 mt-5">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-lg py-2 text-sm">취소</button>
          <button onClick={() => mutation.mutate()} disabled={!form.head_count_out || mutation.isPending}
            className="flex-1 bg-amber-500 text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50">
            {mutation.isPending ? "처리 중..." : "출하 완료"}
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

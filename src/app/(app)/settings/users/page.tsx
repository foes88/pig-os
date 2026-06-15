"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, X } from "lucide-react";
import { useAuthStore } from "@/store/auth.store";
import {
  membersApi,
  type CreateMemberRequest,
  type FarmRole,
  type Member,
} from "@/lib/api/endpoints/members";

const ROLES: FarmRole[] = ["FARM_OWNER", "FARM_MANAGER", "FARM_WORKER", "VET", "VIEWER"];

const ROLE_BADGE: Record<FarmRole, string> = {
  FARM_OWNER:   "bg-purple-50 text-purple-600",
  FARM_MANAGER: "bg-blue-50 text-blue-600",
  FARM_WORKER:  "bg-slate-100 text-slate-600",
  VET:          "bg-green-50 text-green-600",
  VIEWER:       "bg-gray-100 text-gray-500",
};

export default function UsersPage() {
  const t = useTranslations("users");
  const farmId = useAuthStore((s) => s.activeFarmId);
  const myRole = useAuthStore((s) => s.user?.role);
  const queryClient = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);

  // 클라이언트 측 가드 (서버가 최종 권한 강제) — OWNER/MANAGER만 추가 버튼 노출
  const canManage = myRole === "OWNER" || myRole === "MANAGER";

  const { data: members = [], isLoading, isError } = useQuery({
    queryKey: ["members", farmId],
    queryFn: () => membersApi.list(farmId!),
    enabled: !!farmId,
  });

  const updateMutation = useMutation({
    mutationFn: ({ userId, active }: { userId: string; active: boolean }) =>
      membersApi.update(farmId!, userId, { active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["members", farmId] }),
  });

  if (!farmId) return null;

  return (
    <div className="max-w-3xl mx-auto px-7 py-6">
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-xl font-extrabold tracking-tight text-text">{t("title")}</h1>
        {canManage && (
          <button
            onClick={() => setShowAdd(true)}
            className="flex items-center gap-1.5 bg-primary text-white text-sm font-semibold px-3.5 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            <Plus size={15} />
            {t("addMember")}
          </button>
        )}
      </div>
      <p className="text-[13px] text-text3 mb-6">{t("subtitle")}</p>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => <div key={i} className="h-14 bg-border rounded-xl animate-pulse" />)}
        </div>
      ) : isError ? (
        <div className="text-sm text-danger py-12 text-center">—</div>
      ) : members.length === 0 ? (
        <div className="border border-dashed border-border rounded-2xl py-14 text-center text-text3 text-sm">
          {t("empty")}
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-2xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-bg2 text-text3 text-[11px] uppercase tracking-wide">
                <th className="text-left font-semibold px-4 py-2.5">{t("colName")}</th>
                <th className="text-left font-semibold px-4 py-2.5">{t("colEmail")}</th>
                <th className="text-left font-semibold px-4 py-2.5">{t("colRole")}</th>
                <th className="text-left font-semibold px-4 py-2.5">{t("colStatus")}</th>
                {canManage && <th className="text-right font-semibold px-4 py-2.5">{t("colActions")}</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {members.map((m: Member) => (
                <tr key={m.user_id} className="hover:bg-bg2/50 transition">
                  <td className="px-4 py-3 font-semibold text-text">{m.name}</td>
                  <td className="px-4 py-3 text-text2">{m.email ?? "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded-md text-[11px] font-semibold ${ROLE_BADGE[m.role]}`}>
                      {t(`role${m.role}`)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-[11px] font-medium ${m.active ? "text-green-600" : "text-text3"}`}>
                      {m.active ? t("active") : t("inactive")}
                    </span>
                  </td>
                  {canManage && (
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => updateMutation.mutate({ userId: m.user_id, active: !m.active })}
                        disabled={updateMutation.isPending}
                        className="text-xs font-semibold text-text3 hover:text-text transition disabled:opacity-50"
                      >
                        {m.active ? t("deactivate") : t("activate")}
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showAdd && (
        <AddMemberModal
          farmId={farmId}
          onClose={() => setShowAdd(false)}
          onSuccess={() => {
            setShowAdd(false);
            queryClient.invalidateQueries({ queryKey: ["members", farmId] });
          }}
        />
      )}
    </div>
  );
}

function AddMemberModal({
  farmId,
  onClose,
  onSuccess,
}: {
  farmId: string;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const t = useTranslations("users");
  const [form, setForm] = useState<CreateMemberRequest>({
    name: "",
    email: "",
    password: "",
    role: "FARM_WORKER",
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => membersApi.create(farmId, form),
    onSuccess,
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === "string" ? msg : "—");
    },
  });

  const valid = form.name.trim() && form.email.trim() && form.password.length >= 8;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold">{t("modalTitle")}</h2>
          <button onClick={onClose} className="p-1 rounded-md text-text3 hover:text-text hover:bg-bg2 transition">
            <X size={16} />
          </button>
        </div>

        <p className="text-[11px] text-text3 bg-bg2 rounded-lg px-3 py-2 mb-4 leading-relaxed">
          {t("inviteNote")}
        </p>

        <div className="space-y-3">
          <Field label={t("fName")}>
            <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} className="input" />
          </Field>
          <Field label={t("fEmail")}>
            <input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} className="input" />
          </Field>
          <Field label={`${t("fPassword")} (${t("passwordHint")})`}>
            <input type="password" value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} className="input" />
          </Field>
          <Field label={t("fRole")}>
            <select value={form.role} onChange={(e) => setForm((f) => ({ ...f, role: e.target.value as FarmRole }))} className="input">
              {ROLES.map((r) => <option key={r} value={r}>{t(`role${r}`)}</option>)}
            </select>
          </Field>
        </div>

        {error && <p className="text-xs text-red-500 mt-3">{error}</p>}

        <div className="flex gap-2 mt-5">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-lg py-2 text-sm">
            {t("cancel")}
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={!valid || mutation.isPending}
            className="flex-1 bg-primary text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50"
          >
            {t("create")}
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

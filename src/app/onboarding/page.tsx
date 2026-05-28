"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { authApi } from "@/lib/api/endpoints/auth";
import { useAuthStore } from "@/store/auth.store";
import type { OnboardingRequest } from "@/types/api.types";

const STEPS = ["농장 정보", "관리자 계정", "확인"] as const;

const FARM_TYPES = [
  { value: "SOW_FARM",          label: "모돈 전문 농장" },
  { value: "FARROW_TO_FINISH",  label: "일관 사육 농장" },
  { value: "NURSERY",           label: "자돈 농장" },
  { value: "FINISHER",          label: "비육 농장" },
];

const COUNTRIES = [
  { value: "KR", label: "대한민국" },
  { value: "US", label: "미국" },
  { value: "PH", label: "필리핀" },
  { value: "VN", label: "베트남" },
  { value: "TH", label: "태국" },
  { value: "BR", label: "브라질" },
  { value: "MX", label: "멕시코" },
  { value: "CN", label: "중국" },
];

type Form = OnboardingRequest;

export default function OnboardingPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<Form>({
    org_name: "",
    country: "KR",
    name: "",
    email: "",
    password: "",
    farm_name: "",
    farm_type: "FARROW_TO_FINISH",
    sow_count: 100,
    timezone: "Asia/Seoul",
  });
  const [confirmPw, setConfirmPw] = useState("");
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof Form>(k: K, v: Form[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const mutation = useMutation({
    mutationFn: () => authApi.onboard(form),
    onSuccess: (data) => {
      setAuth(
        { id: data.user_id, email: form.email, name: form.name, role: "OWNER", farm_ids: [data.farm_id] },
        data.access_token,
        data.refresh_token,
        data.farm_id,
      );
      document.cookie = `pigos_session=1; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`;
      router.replace("/");
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "가입 중 오류가 발생했습니다.");
    },
  });

  const canProceed = () => {
    if (step === 0) return form.org_name.trim() && form.farm_name.trim() && form.country;
    if (step === 1) return form.name.trim() && form.email.trim() && form.password.length >= 8 && form.password === confirmPw;
    return true;
  };

  const next = () => {
    setError(null);
    if (step < 2) setStep((s) => s + 1);
    else mutation.mutate();
  };

  return (
    <div className="min-h-screen bg-[#0F172A] flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="text-2xl font-extrabold text-white tracking-tight mb-1">
            Pig<span className="text-[#0D7C66]">OS</span>
          </div>
          <p className="text-xs text-slate-400">The operating system for global pig farming</p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {STEPS.map((label, i) => (
            <div key={i} className="flex items-center gap-2">
              <div className={`flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold transition ${
                i < step ? "bg-[#0D7C66] text-white" :
                i === step ? "bg-white text-[#0F172A]" :
                "bg-white/10 text-slate-400"
              }`}>
                {i < step ? "✓" : i + 1}
              </div>
              <span className={`text-xs ${i === step ? "text-white font-medium" : "text-slate-500"}`}>{label}</span>
              {i < STEPS.length - 1 && <span className="text-slate-600 mx-1">→</span>}
            </div>
          ))}
        </div>

        {/* Card */}
        <div className="bg-white/5 border border-white/10 rounded-2xl p-8 backdrop-blur">
          {step === 0 && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-white mb-4">농장 정보</h2>
              <OField label="조직/회사명 *">
                <input value={form.org_name} onChange={(e) => set("org_name", e.target.value)} placeholder="예: 위즈레이크 양돈" className="oinput" />
              </OField>
              <OField label="농장 이름 *">
                <input value={form.farm_name} onChange={(e) => set("farm_name", e.target.value)} placeholder="예: 본장" className="oinput" />
              </OField>
              <OField label="국가 *">
                <select value={form.country} onChange={(e) => set("country", e.target.value)} className="oinput">
                  {COUNTRIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
              </OField>
              <OField label="농장 유형">
                <select value={form.farm_type} onChange={(e) => set("farm_type", e.target.value as Form["farm_type"])} className="oinput">
                  {FARM_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </OField>
              <OField label="모돈 두수">
                <input type="number" min={1} value={form.sow_count ?? ""} onChange={(e) => set("sow_count", Number(e.target.value))} placeholder="예: 500" className="oinput" />
              </OField>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-white mb-4">관리자 계정</h2>
              <OField label="이름 *">
                <input value={form.name} onChange={(e) => set("name", e.target.value)} placeholder="홍길동" className="oinput" />
              </OField>
              <OField label="이메일 *">
                <input type="email" value={form.email} onChange={(e) => set("email", e.target.value)} placeholder="farmer@example.com" className="oinput" />
              </OField>
              <OField label="비밀번호 * (8자 이상)">
                <input type="password" value={form.password} onChange={(e) => set("password", e.target.value)} placeholder="••••••••" className="oinput" />
              </OField>
              <OField label="비밀번호 확인 *">
                <input type="password" value={confirmPw} onChange={(e) => setConfirmPw(e.target.value)} placeholder="••••••••" className="oinput" />
                {confirmPw && form.password !== confirmPw && (
                  <p className="text-xs text-red-400 mt-1">비밀번호가 일치하지 않습니다.</p>
                )}
              </OField>
            </div>
          )}

          {step === 2 && (
            <div>
              <h2 className="text-lg font-bold text-white mb-4">등록 확인</h2>
              <div className="space-y-2 text-sm">
                {[
                  ["조직", form.org_name],
                  ["농장", form.farm_name],
                  ["국가", COUNTRIES.find((c) => c.value === form.country)?.label ?? form.country],
                  ["유형", FARM_TYPES.find((t) => t.value === form.farm_type)?.label ?? form.farm_type ?? ""],
                  ["모돈", `${form.sow_count ?? "-"}두`],
                  ["이름", form.name],
                  ["이메일", form.email],
                ].map(([label, value]) => (
                  <div key={label} className="flex justify-between py-1.5 border-b border-white/10">
                    <span className="text-slate-400">{label}</span>
                    <span className="text-white font-medium">{value}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-500 mt-4">
                무료로 시작합니다. 신용카드 불필요.
              </p>
            </div>
          )}

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 mt-4">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          <div className="flex gap-3 mt-6">
            {step > 0 && (
              <button
                onClick={() => setStep((s) => s - 1)}
                className="flex-1 border border-white/20 text-white rounded-xl py-2.5 text-sm hover:bg-white/5 transition"
              >
                이전
              </button>
            )}
            <button
              onClick={next}
              disabled={!canProceed() || mutation.isPending}
              className="flex-1 bg-[#0D7C66] hover:bg-[#0D7C66]/90 disabled:opacity-50 text-white font-semibold rounded-xl py-2.5 text-sm transition"
            >
              {mutation.isPending ? "처리 중..." : step === 2 ? "무료로 시작하기" : "다음"}
            </button>
          </div>
        </div>

        <p className="text-center text-xs text-slate-600 mt-4">
          이미 계정이 있으신가요?{" "}
          <a href="/login" className="text-[#0D7C66] hover:underline">로그인</a>
        </p>
      </div>

      <style>{`
        .oinput {
          width: 100%;
          padding: 0.625rem 0.875rem;
          border-radius: 0.5rem;
          background: rgba(255,255,255,0.07);
          border: 1px solid rgba(255,255,255,0.12);
          color: white;
          font-size: 0.875rem;
          outline: none;
          transition: border-color 0.15s;
        }
        .oinput:focus { border-color: #0D7C66; }
        .oinput option { background: #1E293B; color: white; }
      `}</style>
    </div>
  );
}

function OField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-medium text-slate-300 mb-1.5">{label}</label>
      {children}
    </div>
  );
}

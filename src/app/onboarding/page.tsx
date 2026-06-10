"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { authApi } from "@/lib/api/endpoints/auth";
import { useAuthStore } from "@/store/auth.store";
import type { OnboardingRequest } from "@/types/api.types";

const STEPS = ["Farm Info", "Account", "Confirm"] as const;

const FARM_TYPES = [
  { value: "SOW_FARM",         label: "Sow farm" },
  { value: "FARROW_TO_FINISH", label: "Farrow-to-finish" },
  { value: "NURSERY",          label: "Nursery" },
  { value: "FINISHER",         label: "Finisher" },
];

const COUNTRIES = [
  { value: "KR", label: "South Korea" },
  { value: "US", label: "United States" },
  { value: "CN", label: "China" },
  { value: "VN", label: "Vietnam" },
  { value: "TH", label: "Thailand" },
  { value: "PH", label: "Philippines" },
  { value: "BR", label: "Brazil" },
  { value: "MX", label: "Mexico" },
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
      setError(typeof detail === "string" ? detail : "Something went wrong. Please try again.");
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
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-[520px]">

        {/* Logo */}
        <div className="flex justify-center mb-8">
          <Image
            src="/logos/pigos-logo-horizontal-light.svg"
            alt="PigOS"
            width={140}
            height={53}
            className="object-contain"
            priority
          />
        </div>

        {/* Step indicator */}
        <div className="flex items-center justify-center gap-0 mb-8">
          {STEPS.map((label, i) => (
            <div key={i} className="flex items-center">
              <div className="flex flex-col items-center gap-1.5">
                <div className={`flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold border-2 transition-all ${
                  i < step
                    ? "bg-[#2563EB] border-[#2563EB] text-white"
                    : i === step
                    ? "bg-white border-[#2563EB] text-[#2563EB]"
                    : "bg-white border-slate-200 text-slate-400"
                }`}>
                  {i < step ? (
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M20 6 9 17l-5-5"/>
                    </svg>
                  ) : (
                    i + 1
                  )}
                </div>
                <span className={`text-xs ${i === step ? "text-slate-700 font-medium" : "text-slate-400"}`}>
                  {label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div className={`h-px w-16 mx-3 mb-5 ${i < step ? "bg-[#2563EB]" : "bg-slate-200"}`} />
              )}
            </div>
          ))}
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8">
          {step === 0 && (
            <div className="space-y-4">
              <div className="mb-6">
                <h2 className="text-lg font-bold text-slate-900">Farm information</h2>
                <p className="text-sm text-slate-500 mt-0.5">Tell us about your farm operation</p>
              </div>
              <Field label="Organization / Company *">
                <input value={form.org_name} onChange={(e) => set("org_name", e.target.value)}
                  placeholder="e.g. WiseLake Farm Co." className="fin" />
              </Field>
              <Field label="Farm name *">
                <input value={form.farm_name} onChange={(e) => set("farm_name", e.target.value)}
                  placeholder="e.g. Main Farm" className="fin" />
              </Field>
              <div className="grid grid-cols-2 gap-4">
                <Field label="Country *">
                  <select value={form.country} onChange={(e) => set("country", e.target.value)} className="fin">
                    {COUNTRIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                  </select>
                </Field>
                <Field label="Farm type">
                  <select value={form.farm_type} onChange={(e) => set("farm_type", e.target.value as Form["farm_type"])} className="fin">
                    {FARM_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </Field>
              </div>
              <Field label="Sow count">
                <input type="number" min={1} value={form.sow_count ?? ""}
                  onChange={(e) => set("sow_count", Number(e.target.value))}
                  placeholder="e.g. 500" className="fin" />
              </Field>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <div className="mb-6">
                <h2 className="text-lg font-bold text-slate-900">Create your account</h2>
                <p className="text-sm text-slate-500 mt-0.5">You'll use this to sign in to PigOS</p>
              </div>
              <Field label="Full name *">
                <input value={form.name} onChange={(e) => set("name", e.target.value)}
                  placeholder="e.g. John Kim" className="fin" />
              </Field>
              <Field label="Email address *">
                <input type="email" value={form.email} onChange={(e) => set("email", e.target.value)}
                  placeholder="farmer@example.com" className="fin" />
              </Field>
              <Field label="Password * (min. 8 characters)">
                <input type="password" value={form.password} onChange={(e) => set("password", e.target.value)}
                  placeholder="••••••••" className="fin" />
              </Field>
              <Field label="Confirm password *">
                <input type="password" value={confirmPw} onChange={(e) => setConfirmPw(e.target.value)}
                  placeholder="••••••••" className={`fin ${confirmPw && form.password !== confirmPw ? "!border-red-400" : ""}`} />
                {confirmPw && form.password !== confirmPw && (
                  <p className="text-xs text-red-500 mt-1">Passwords do not match</p>
                )}
              </Field>
            </div>
          )}

          {step === 2 && (
            <div>
              <div className="mb-6">
                <h2 className="text-lg font-bold text-slate-900">Confirm & start</h2>
                <p className="text-sm text-slate-500 mt-0.5">Review your details before creating your account</p>
              </div>
              <div className="rounded-xl border border-slate-200 overflow-hidden">
                {[
                  ["Organization", form.org_name],
                  ["Farm", form.farm_name],
                  ["Country", COUNTRIES.find((c) => c.value === form.country)?.label ?? form.country],
                  ["Farm type", FARM_TYPES.find((t) => t.value === form.farm_type)?.label ?? form.farm_type ?? ""],
                  ["Sow count", `${form.sow_count ?? "-"} head`],
                  ["Name", form.name],
                  ["Email", form.email],
                ].map(([label, value], idx, arr) => (
                  <div key={label} className={`flex justify-between px-4 py-3 text-sm ${idx < arr.length - 1 ? "border-b border-slate-100" : ""}`}>
                    <span className="text-slate-500">{label}</span>
                    <span className="text-slate-900 font-medium">{value}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-400 mt-4 flex items-center gap-1.5">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
                Free to start. No credit card required.
              </p>
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2.5 bg-red-50 border border-red-200 rounded-lg px-4 py-3 mt-4">
              <svg className="w-4 h-4 text-red-500 mt-0.5 shrink-0" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div className="flex gap-3 mt-6">
            {step > 0 && (
              <button onClick={() => setStep((s) => s - 1)}
                className="flex-1 h-11 border border-slate-300 text-slate-700 rounded-lg text-sm
                  font-medium hover:bg-slate-50 transition">
                Back
              </button>
            )}
            <button onClick={next}
              disabled={!canProceed() || mutation.isPending}
              className="flex-1 h-11 bg-[#2563EB] hover:bg-[#1D4ED8] disabled:opacity-50
                text-white font-semibold rounded-lg text-sm transition shadow-sm shadow-blue-200/60">
              {mutation.isPending ? "Creating account…" : step === 2 ? "Get started free" : "Continue"}
            </button>
          </div>
        </div>

        <p className="text-center text-sm text-slate-500 mt-5">
          Already have an account?{" "}
          <a href="/login" className="text-[#2563EB] hover:underline font-medium">Sign in</a>
        </p>
        <p className="text-center text-xs text-slate-400 mt-3">© 2026 WiseLake Inc.</p>
      </div>

      <style>{`
        .fin {
          width: 100%;
          height: 44px;
          padding: 0 0.875rem;
          border-radius: 0.5rem;
          background: #fff;
          border: 1px solid #CBD5E1;
          color: #0f172a;
          font-size: 0.875rem;
          outline: none;
          transition: border-color 0.15s, box-shadow 0.15s;
        }
        .fin:focus {
          border-color: #2563EB;
          box-shadow: 0 0 0 3px rgba(37,99,235,0.12);
        }
        .fin::placeholder { color: #94a3b8; }
      `}</style>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1.5">{label}</label>
      {children}
    </div>
  );
}

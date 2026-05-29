"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { authApi } from "@/lib/api/endpoints/auth";
import { useAuthStore } from "@/store/auth.store";

const schema = z.object({
  email: z.string().email("올바른 이메일을 입력하세요"),
  password: z.string().min(1, "비밀번호를 입력하세요"),
});
type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    setServerError(null);
    try {
      const data = await authApi.login(values);

      // Save to Zustand store (persisted to localStorage)
      setAuth(
        {
          id: data.user_id,
          email: data.email,
          name: data.name,
          role: data.role as "OWNER" | "MANAGER" | "WORKER" | "VET",
          farm_ids: data.farm_ids,
        },
        data.access_token,
        data.refresh_token,
        data.farm_ids[0],
      );

      // Set lightweight session cookie for middleware route protection
      document.cookie = `pigos_session=1; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`;

      const next = searchParams.get("next") ?? "/";
      router.replace(next);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 401) {
        setServerError("이메일 또는 비밀번호가 올바르지 않습니다.");
      } else if (status === 422) {
        setServerError("입력 형식을 확인해 주세요.");
      } else {
        setServerError("서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.");
      }
    }
  };

  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl p-8 backdrop-blur">
      <h1 className="text-xl font-bold text-white mb-6">로그인</h1>

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        {/* Email */}
        <div>
          <label className="block text-sm text-slate-300 mb-1.5">이메일</label>
          <input
            type="email"
            autoComplete="email"
            placeholder="farmer@example.com"
            {...register("email")}
            className={`w-full px-4 py-2.5 rounded-lg bg-white/10 border text-white placeholder:text-slate-500
              text-sm outline-none transition focus:border-[#2563EB]
              ${errors.email ? "border-red-500" : "border-white/20"}`}
          />
          {errors.email && (
            <p className="text-xs text-red-400 mt-1">{errors.email.message}</p>
          )}
        </div>

        {/* Password */}
        <div>
          <label className="block text-sm text-slate-300 mb-1.5">비밀번호</label>
          <input
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            {...register("password")}
            className={`w-full px-4 py-2.5 rounded-lg bg-white/10 border text-white placeholder:text-slate-500
              text-sm outline-none transition focus:border-[#2563EB]
              ${errors.password ? "border-red-500" : "border-white/20"}`}
          />
          {errors.password && (
            <p className="text-xs text-red-400 mt-1">{errors.password.message}</p>
          )}
        </div>

        {/* Server error */}
        {serverError && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3">
            <p className="text-sm text-red-400">{serverError}</p>
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-[#2563EB] hover:bg-blue-500 disabled:opacity-50
            text-white font-semibold py-2.5 rounded-lg text-sm transition mt-2"
        >
          {isSubmitting ? "로그인 중..." : "로그인"}
        </button>
      </form>

      <p className="text-center text-xs text-slate-500 mt-6">
        계정이 없으신가요?{" "}
        <a href="/onboarding" className="text-[#2563EB] hover:underline">
          무료로 시작하기
        </a>
      </p>
    </div>
  );
}

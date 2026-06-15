"use client";
import { useTranslations } from "next-intl";

export default function VerifyEmailPage() {
  const t = useTranslations("util");
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0F1B2D] px-6">
      <div className="bg-white rounded-2xl shadow-2xl p-10 w-full max-w-md text-center">
        <div className="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center mx-auto mb-6">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 7l-10 5L2 7"/>
          </svg>
        </div>
        <h1 className="text-2xl font-extrabold text-[#0F172A] tracking-tight mb-2">{t("veTitle")}</h1>
        <p className="text-sm text-gray-500 leading-relaxed mb-1">{t("veDesc1")}</p>
        <p className="text-xs text-gray-400 mb-8">{t("veDesc2")}</p>
        <button className="w-full bg-[#0D1B3E] text-white py-3.5 rounded-xl text-sm font-bold hover:opacity-90 transition">
          {t("veOpen")}
        </button>
        <p className="mt-5 text-xs text-gray-400">
          {t("veNoEmail")}{" "}
          <span className="text-blue-600 font-semibold cursor-pointer">{t("veResend")}</span>
          {" · "}
          <span className="text-gray-400 cursor-pointer">{t("veChange")}</span>
        </p>
      </div>
    </div>
  );
}

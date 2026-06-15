"use client";
import { useTranslations } from "next-intl";

export default function UpdatePage() {
  const t = useTranslations("util");
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-6">
      <div className="bg-surface border border-border rounded-2xl shadow-xl p-10 w-full max-w-md text-center">
        <div className="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center mx-auto mb-6">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 12a9 9 0 1 1-6.2-8.6"/><path d="M21 3v6h-6"/>
          </svg>
        </div>
        <h1 className="text-2xl font-extrabold text-text tracking-tight mb-2">{t("upTitle")}</h1>
        <p className="text-sm text-text2 leading-relaxed mb-1">{t("upDesc")}</p>
        <p className="text-xs text-text3 font-mono mb-6">{t("upVersion")}</p>
        <div className="bg-background rounded-xl p-4 text-left mb-6">
          <p className="text-xs font-bold text-text3 mb-3">{t("upWhat")}</p>
          {[t("upN1"), t("upN2"), t("upN3")].map((x, i) => (
            <div key={i} className="flex items-center gap-2 py-1.5 text-sm text-text2">
              <span className="text-success font-bold">✓</span>{x}
            </div>
          ))}
        </div>
        <button className="w-full bg-navy text-white py-4 rounded-xl text-base font-bold hover:opacity-90 transition">
          {t("upNow")}
        </button>
      </div>
    </div>
  );
}

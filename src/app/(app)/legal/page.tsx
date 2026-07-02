"use client";
import { useState } from "react";
import { useTranslations } from "next-intl";

export default function LegalPage() {
  const t = useTranslations("legal");
  const [tab, setTab] = useState<"terms" | "privacy">("terms");
  const articles = t.raw(tab) as { h: string; b: string }[];
  return (
    <div className="max-w-3xl mx-auto px-7 py-6">
      <h1 className="text-xl font-extrabold tracking-tight mb-3">{t("title")}</h1>
      <p className="text-xs text-text3 mb-5 bg-amber-soft border border-warning/40 rounded-lg px-3 py-2">{t("disclaimer")}</p>
      <div className="flex gap-2 mb-5">
        {([["terms", t("tabTerms")], ["privacy", t("tabPrivacy")]] as const).map(([k, l]) => (
          <button key={k} onClick={() => setTab(k as "terms" | "privacy")}
            className={`px-5 py-2 rounded-xl text-sm font-semibold border transition ${
              tab === k ? "bg-navy text-white border-navy" : "bg-surface border-border text-text2 hover:bg-border"
            }`}>{l}</button>
        ))}
      </div>
      <div className="bg-surface border border-border rounded-2xl p-6">
        <p className="text-[11px] text-text3 font-mono mb-5">{t("revised")}</p>
        <div className="space-y-5">
          {articles.map(({ h, b }, i) => (
            <div key={i}>
              <div className="text-sm font-bold text-text mb-1.5">{h}</div>
              <p className="text-sm text-text2 leading-relaxed">{b}</p>
            </div>
          ))}
        </div>
      </div>
      <p className="text-xs text-text3 text-center mt-4">
        {t("footer")} <span className="text-primary">legal@pigos.io</span>
      </p>
    </div>
  );
}

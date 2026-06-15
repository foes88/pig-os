"use client";
import { useTranslations } from "next-intl";

const INVOICES = [
  ["2026-05-15", "$179.00"],
  ["2026-04-15", "$179.00"],
  ["2026-03-15", "$179.00"],
];

export default function BillingPage() {
  const t = useTranslations("billing");
  return (
    <div className="max-w-3xl mx-auto px-7 py-6">
      <h1 className="text-xl font-extrabold tracking-tight mb-5">{t("title")}</h1>

      {/* Current plan */}
      <div className="bg-navy rounded-2xl p-6 text-white mb-4">
        <div className="flex items-start justify-between mb-5">
          <div>
            <p className="text-[11px] font-bold opacity-60 tracking-widest font-mono">{t("currentPlan")}</p>
            <p className="text-2xl font-extrabold tracking-tight mt-1">{t("planName")}</p>
            <p className="text-xs opacity-60 mt-1">{t("nextBilling")}</p>
          </div>
          <div className="text-right font-mono">
            <span className="text-3xl font-extrabold">$179</span>
            <span className="text-xs opacity-60">{t("perMonth")}</span>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="bg-white/15 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-white/20 transition">{t("changePlan")}</button>
          <button className="border border-white/25 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-white/10 transition">{t("cancel")}</button>
        </div>
      </div>

      {/* Payment method */}
      <div className="bg-surface border border-border rounded-2xl p-5 mb-4">
        <p className="text-xs font-bold text-text3 font-mono mb-4">{t("paymentMethod")}</p>
        <div className="flex items-center gap-4">
          <div className="w-12 h-8 rounded border border-border bg-background flex items-center justify-center text-[11px] font-bold font-mono">VISA</div>
          <div className="flex-1">
            <p className="text-sm font-semibold font-mono text-text">•••• •••• •••• 4242</p>
            <p className="text-xs text-text3">{t("expires")}</p>
          </div>
          <button className="text-xs font-semibold text-primary hover:underline">{t("change")}</button>
        </div>
      </div>

      {/* Invoices */}
      <div className="bg-surface border border-border rounded-2xl p-5">
        <p className="text-xs font-bold text-text3 font-mono mb-4">{t("history")}</p>
        {INVOICES.map(([date, amount], i) => (
          <div key={i} className={`flex items-center py-3 ${i < INVOICES.length - 1 ? "border-b border-border" : ""}`}>
            <span className="text-sm font-mono text-text2 flex-1">{date}</span>
            <span className="text-sm font-bold font-mono text-text mr-4">{amount}</span>
            <span className="text-[11px] font-semibold text-success bg-green-50 border border-green-100 px-2 py-0.5 rounded-md mr-4">{t("paid")}</span>
            <button className="text-xs font-semibold text-primary hover:underline">{t("receipt")}</button>
          </div>
        ))}
      </div>
    </div>
  );
}

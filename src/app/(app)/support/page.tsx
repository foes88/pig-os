"use client";
import { useState } from "react";
import { useTranslations } from "next-intl";

export default function SupportPage() {
  const t = useTranslations("support");
  const [open, setOpen] = useState<number | null>(0);
  const faqs = t.raw("faqs") as { q: string; a: string }[];
  const contacts: [string, string, string][] = [
    ["💬", t("chat"), t("chatHours")],
    ["📧", t("email"), "help@pigos.io"],
    ["📞", t("phone"), "1588-0000"],
  ];

  return (
    <div className="max-w-3xl mx-auto px-7 py-6">
      <h1 className="text-xl font-extrabold tracking-tight mb-5">{t("title")}</h1>

      <div className="grid grid-cols-3 gap-3 mb-7">
        {contacts.map(([ic, label, s], i) => (
          <div key={i} className="bg-surface border border-border rounded-2xl p-5">
            <div className="text-2xl mb-2">{ic}</div>
            <div className="text-sm font-bold text-text">{label}</div>
            <div className="text-xs text-text3 mt-1">{s}</div>
          </div>
        ))}
      </div>

      <p className="text-xs font-semibold text-text3 tracking-wider font-mono mb-3">{t("faqTitle")}</p>
      <div className="space-y-2">
        {faqs.map(({ q, a }, i) => (
          <div key={i} className="bg-surface border border-border rounded-2xl overflow-hidden">
            <button
              onClick={() => setOpen(open === i ? null : i)}
              className="w-full flex items-center justify-between px-5 py-4 text-left"
            >
              <span className="text-sm font-semibold text-text">{q}</span>
              <span className="text-text3 text-xs ml-3">{open === i ? "▲" : "▼"}</span>
            </button>
            {open === i && (
              <div className="px-5 pb-4 text-sm text-text2 leading-relaxed border-t border-border pt-3">
                {a}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

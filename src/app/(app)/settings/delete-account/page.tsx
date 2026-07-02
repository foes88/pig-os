"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { canOwn } from "@/lib/auth/permissions";
import { useActiveRole } from "@/lib/auth/useActiveRole";

export default function DeleteAccountPage() {
  const t = useTranslations("deleteAccount");
  const [confirm, setConfirm] = useState("");
  const router = useRouter();
  const confirmWord = t("confirmWord");
  const canDelete = confirm === confirmWord;
  const isOwner = canOwn(useActiveRole());

  // 계정/농장 삭제는 소유자 전용
  if (!isOwner) {
    return (
      <div className="max-w-xl mx-auto px-7 py-6">
        <h1 className="text-xl font-extrabold tracking-tight mb-5">{t("title")}</h1>
        <div className="bg-surface border border-border rounded-2xl p-6 text-center text-sm text-text3">
          {t("ownerOnly")}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto px-7 py-6">
      <h1 className="text-xl font-extrabold tracking-tight mb-5">{t("title")}</h1>
      <div className="bg-surface border border-border rounded-2xl p-6">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-11 h-11 rounded-xl bg-red-soft flex items-center justify-center shrink-0">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#DC2626" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
          </div>
          <div>
            <div className="text-base font-bold text-text">{t("sure")}</div>
            <div className="text-xs text-text3 mt-0.5">{t("irreversible")}</div>
          </div>
        </div>
        <div className="bg-red-soft border border-red-100 rounded-xl p-4 mb-5">
          <div className="text-xs font-bold text-danger mb-2">{t("lostTitle")}</div>
          {[t("l1"), t("l2"), t("l3"), t("l4")].map((x, i) => (
            <div key={i} className="text-xs text-text2 flex items-center gap-2 py-1">
              <span className="text-danger font-bold">✕</span>{x}
            </div>
          ))}
        </div>
        <p className="text-xs text-text3 leading-relaxed mb-5">
          {t("exportPre")}
          <span className="text-primary font-semibold cursor-pointer">{t("exportLink")}</span>{t("exportPost")}
          {" "}{t("recovery")}
        </p>
        <div className="mb-5">
          <label className="block text-xs font-semibold text-text2 mb-2">
            {t("typeToConfirm", { word: confirmWord })}
          </label>
          <input
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder={confirmWord}
            className="input w-full"
          />
        </div>
        <div className="flex gap-2">
          <button onClick={() => router.back()}
            className="flex-1 bg-surface border border-border text-text2 py-3 rounded-xl text-sm font-semibold hover:bg-border transition">
            {t("cancel")}
          </button>
          <button
            disabled={!canDelete}
            className="flex-1 bg-danger text-white py-3 rounded-xl text-sm font-bold disabled:opacity-40 hover:opacity-90 transition">
            {t("deleteForever")}
          </button>
        </div>
      </div>
    </div>
  );
}

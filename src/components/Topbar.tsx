"use client";

import { Bell, Search } from "lucide-react";
import { useTranslations } from "next-intl";
import { useAuthStore } from "@/store/auth.store";
import { visibleLocales } from "@/i18n/config";
import { FarmSwitcher } from "@/components/FarmSwitcher";

import type { Locale } from "@/i18n/config";

// LANG_LABELS는 언어 선택기 표시명(로케일 불변 상수 — 번역 대상 아님). search/qi는 topbar 네임스페이스.
const LANG_LABELS: Record<Locale, string> = {
  en: "EN", ko: "KO", zh: "中文", es: "ES", vi: "VI", th: "ไทย", pt: "PT", ru: "RU",
};

interface TopbarProps {
  lang?: Locale;
  onLangToggle?: (l: Locale) => void;
  onQuickInput?: () => void;
  onBell?: () => void;
  alertCount?: number;
}

export function Topbar({
  lang = "ko",
  onLangToggle,
  onQuickInput,
  onBell,
  alertCount = 0,
}: TopbarProps) {
  const t = useTranslations("topbar");
  // 한국어 가시성은 system_role 기준(농장 role이 아니라 플랫폼 권한 — 코드리뷰 #2).
  const systemRole = useAuthStore((s) => s.user?.system_role);
  // 한국어는 플랫폼 관리자만. 현재 lang이 목록에 없으면(엣지) 깨지지 않게 포함.
  const localeOpts = visibleLocales(systemRole);
  const langOpts = localeOpts.includes(lang) ? localeOpts : [lang, ...localeOpts];

  return (
    <header className="h-14 flex-shrink-0 bg-bg border-b border-border flex items-center px-5 gap-3">
      {/* Farm switcher (멀티팜: 접근 가능 농장 전환) */}
      <FarmSwitcher />

      {/* Search */}
      <div className="flex-1 max-w-[360px] relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-faint" size={14} />
        <input
          placeholder={t("search")}
          className="w-full bg-surface border border-border text-text text-xs pl-8 pr-10 py-2 rounded-lg outline-none focus:border-primary transition"
        />
        <span className="absolute right-2.5 top-1/2 -translate-y-1/2 font-mono text-[9px] text-faint bg-panel-hi px-1.5 py-0.5 rounded">
          ⌘K
        </span>
      </div>

      <div className="flex items-center gap-2 ml-auto">
        {/* Lang select */}
        <select
          value={lang}
          data-testid="language-switcher"
          onChange={(e) => onLangToggle?.(e.target.value as Locale)}
          className="bg-surface border border-border text-text text-[11px] font-bold px-2 py-1.5 rounded-md outline-none focus:border-primary cursor-pointer"
        >
          {langOpts.map((l) => (
            <option key={l} value={l}>{LANG_LABELS[l]}</option>
          ))}
        </select>

        {/* Bell */}
        <button
          onClick={onBell}
          className="relative p-2 rounded-lg text-muted hover:bg-bg2 hover:text-text transition"
        >
          <Bell size={18} />
          {alertCount > 0 && (
            <span className="absolute top-1 right-1 min-w-[14px] h-3.5 px-1 rounded-full bg-red text-white font-mono text-[9px] font-bold flex items-center justify-center">
              {alertCount}
            </span>
          )}
        </button>

        {/* Quick Input */}
        <button
          onClick={onQuickInput}
          className="flex items-center gap-1.5 bg-navy text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-primary transition"
        >
          <span className="text-sm font-bold leading-none">+</span>
          {t("qi")}
        </button>
      </div>
    </header>
  );
}

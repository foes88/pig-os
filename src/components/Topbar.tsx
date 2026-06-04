"use client";

import type { Locale } from "@/i18n/config";

const LABELS: Record<Locale, { search: string; qi: string }> = {
  en: { search: "Search sow ID, batch, room…",    qi: "Quick Input"    },
  ko: { search: "모돈 ID, 배치, 구역 검색…",         qi: "빠른 입력"      },
  zh: { search: "搜索母猪ID、批次、栏位…",             qi: "快速录入"       },
  es: { search: "Buscar cerda ID, lote, sala…",   qi: "Entrada Rápida" },
  vi: { search: "Tìm số nái, lô, khu…",           qi: "Nhập nhanh"     },
};

const LANG_LABELS: Record<Locale, string> = {
  en: "EN", ko: "KO", zh: "中文", es: "ES", vi: "VI",
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
  const t = LABELS[lang] ?? LABELS.en;

  return (
    <header className="h-14 flex-shrink-0 bg-bg border-b border-border flex items-center px-5 gap-3">
      {/* Search */}
      <div className="flex-1 max-w-[360px] relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-faint text-xs">🔍</span>
        <input
          placeholder={t.search}
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
          onChange={(e) => onLangToggle?.(e.target.value as Locale)}
          className="bg-surface border border-border text-text text-[11px] font-bold px-2 py-1.5 rounded-md outline-none focus:border-primary cursor-pointer"
        >
          {(Object.keys(LANG_LABELS) as Locale[]).map((l) => (
            <option key={l} value={l}>{LANG_LABELS[l]}</option>
          ))}
        </select>

        {/* Bell */}
        <button
          onClick={onBell}
          className="relative p-2 rounded-lg text-muted hover:bg-bg2 hover:text-text transition"
        >
          <span className="text-base">🔔</span>
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
          {t.qi}
        </button>
      </div>
    </header>
  );
}

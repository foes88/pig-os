"use client";

interface TopbarProps {
  lang?: "en" | "ko";
  onLangToggle?: (l: "en" | "ko") => void;
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
  const t = lang === "ko"
    ? { search: "모돈 ID, 배치, 구역 검색…", qi: "빠른 입력" }
    : { search: "Search sow ID, batch, room…", qi: "Quick Input" };

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
        {/* Lang toggle */}
        <div className="flex bg-surface border border-border rounded-md overflow-hidden">
          {(["en", "ko"] as const).map((l) => (
            <button
              key={l}
              onClick={() => onLangToggle?.(l)}
              className={`px-2.5 py-1 text-[11px] font-bold tracking-wider transition ${
                lang === l
                  ? "bg-text text-bg"
                  : "text-muted hover:text-text"
              }`}
            >
              {l.toUpperCase()}
            </button>
          ))}
        </div>

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

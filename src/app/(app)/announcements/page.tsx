"use client";
import { useTranslations } from "next-intl";

// 비텍스트 메타(색상/날짜/고정)는 코드, 텍스트(tag/title/body)는 i18n items[]에서
const META = [
  { tagColor: "text-primary bg-blue-50 border-blue-100", date: "2026-05-28", pinned: true },
  { tagColor: "text-warning bg-amber-50 border-amber-100", date: "2026-05-25", pinned: false },
  { tagColor: "text-success bg-green-50 border-green-100", date: "2026-05-10", pinned: false },
];

export default function AnnouncementsPage() {
  const t = useTranslations("announcements");
  const items = t.raw("items") as { tag: string; title: string; body: string }[];
  return (
    <div className="max-w-3xl mx-auto px-7 py-6">
      <h1 className="text-xl font-extrabold tracking-tight mb-5">{t("title")}</h1>
      <div className="space-y-3">
        {items.map((n, i) => (
          <div key={i} className="bg-surface border border-border rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-3">
              {META[i]?.pinned && <span className="text-sm">📌</span>}
              <span className={`text-[11px] font-bold font-mono px-2 py-0.5 rounded-md border ${META[i]?.tagColor ?? ""}`}>{n.tag}</span>
              <span className="text-[11px] text-text3 font-mono ml-auto">{META[i]?.date}</span>
            </div>
            <div className="text-sm font-bold text-text mb-2">{n.title}</div>
            <p className="text-sm text-text2 leading-relaxed">{n.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

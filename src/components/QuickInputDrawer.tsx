"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

interface QuickInputDrawerProps {
  open: boolean;
  onClose: () => void;
  lang?: "en" | "ko";
}

const EVENTS = [
  { id: "mating",    icon: "💉", color: "#2563EB", soft: "#EFF6FF", label: { en: "Mating",    ko: "교배"   } },
  { id: "farrowing", icon: "🐖", color: "#059669", soft: "#ECFDF5", label: { en: "Farrowing", ko: "분만"   } },
  { id: "weaning",   icon: "🌱", color: "#D97706", soft: "#FFFBEB", label: { en: "Weaning",   ko: "이유"   } },
  { id: "repro",     icon: "⚠️", color: "#DC2626", soft: "#FEF2F2", label: { en: "Repro Event", ko: "임신사고" } },
  { id: "cull",      icon: "📋", color: "#64748B", soft: "#F8FAFC", label: { en: "Cull / Death", ko: "도폐사" } },
  { id: "piglet",    icon: "🐽", color: "#7C3AED", soft: "#F5F3FF", label: { en: "Piglet Group", ko: "자돈 그룹" } },
  { id: "finisher",  icon: "🏭", color: "#0D1B3E", soft: "#F0F4FF", label: { en: "Finisher",  ko: "비육돈" } },
  { id: "foster",    icon: "🔄", color: "#0891B2", soft: "#ECFEFF", label: { en: "Foster",    ko: "양자"   } },
];

export function QuickInputDrawer({ open, onClose, lang = "ko" }: QuickInputDrawerProps) {
  const router = useRouter();
  const [selected, setSelected] = useState<string | null>(null);

  const handleSelect = (id: string) => {
    setSelected(id);
    onClose();
    if (["mating", "farrowing", "weaning", "repro", "cull"].includes(id)) {
      const tabMap: Record<string, string> = {
        mating: "mating", farrowing: "farrowing", weaning: "weaning",
        repro: "repro", cull: "cull",
      };
      router.push(`/record?tab=${tabMap[id]}`);
    } else if (id === "piglet") {
      router.push("/piglets");
    } else if (id === "finisher") {
      router.push("/finishers");
    } else if (id === "foster") {
      router.push("/record?tab=foster");
    }
  };

  const title = lang === "ko" ? "빠른 입력" : "Quick Input";
  const sub = lang === "ko" ? "이벤트 유형을 선택하세요" : "Select an event type";

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/30 z-[90] backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Drawer — bottom sheet on mobile, centered on desktop */}
      <div className="fixed bottom-0 left-0 right-0 md:bottom-auto md:left-1/2 md:top-1/2 md:-translate-x-1/2 md:-translate-y-1/2 md:w-[480px] z-[100] bg-surface rounded-t-2xl md:rounded-2xl shadow-2xl border border-border">
        {/* Handle (mobile) */}
        <div className="flex justify-center pt-3 pb-1 md:hidden">
          <div className="w-10 h-1 bg-border rounded-full" />
        </div>

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div>
            <h2 className="text-base font-bold text-text">{title}</h2>
            <p className="text-xs text-muted mt-0.5">{sub}</p>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-full bg-bg2 flex items-center justify-center text-muted hover:text-text transition text-sm"
          >
            ✕
          </button>
        </div>

        {/* Event grid */}
        <div className="grid grid-cols-4 gap-3 p-5">
          {EVENTS.map((ev) => (
            <button
              key={ev.id}
              onClick={() => handleSelect(ev.id)}
              className="flex flex-col items-center gap-2 p-3 rounded-xl border border-border hover:border-primary transition group"
              style={{ background: ev.soft }}
            >
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
                style={{ background: ev.color + "18" }}
              >
                {ev.icon}
              </div>
              <span className="text-[11px] font-semibold text-text2 text-center leading-tight">
                {ev.label[lang]}
              </span>
            </button>
          ))}
        </div>

        <div className="pb-6 md:pb-4" />
      </div>
    </>
  );
}

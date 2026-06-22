"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Syringe,
  Baby,
  Sprout,
  AlertTriangle,
  ClipboardX,
  Layers,
  Beef,
  Repeat,
  X,
} from "lucide-react";
import type { Locale } from "@/i18n/config";

interface QuickInputDrawerProps {
  open: boolean;
  onClose: () => void;
  lang?: Locale;
}

type L = Record<Locale, string>;

const EVENTS: { id: string; icon: React.ElementType; color: string; soft: string; label: L }[] = [
  { id: "mating",    icon: Syringe,       color: "#0F6342", soft: "#E8F6EF", label: { en: "Mating",       ko: "교배",    zh: "配种",   es: "Monta",          vi: "Phối giống" } },
  { id: "farrowing", icon: Baby,          color: "#059669", soft: "#ECFDF5", label: { en: "Farrowing",    ko: "분만",    zh: "分娩",   es: "Parto",          vi: "Đẻ" } },
  { id: "weaning",   icon: Sprout,        color: "#D97706", soft: "#FFFBEB", label: { en: "Weaning",      ko: "이유",    zh: "断奶",   es: "Destete",        vi: "Cai sữa" } },
  { id: "repro",     icon: AlertTriangle, color: "#DC2626", soft: "#FEF2F2", label: { en: "Repro Event",  ko: "임신사고", zh: "繁殖事故", es: "Evento Repro",  vi: "Sự cố sinh sản" } },
  { id: "cull",      icon: ClipboardX,    color: "#64748B", soft: "#F8FAFC", label: { en: "Cull / Death", ko: "도폐사",  zh: "淘汰/死亡", es: "Eliminación",  vi: "Loại/Chết" } },
  { id: "piglet",    icon: Layers,        color: "#5F4B2C", soft: "#ECE4D3", label: { en: "Piglet Group", ko: "자돈 그룹", zh: "仔猪组",  es: "Grupo Lechones", vi: "Nhóm heo con" } },
  { id: "finisher",  icon: Beef,          color: "#0D1B3E", soft: "#F0F4FF", label: { en: "Finisher",     ko: "비육돈",  zh: "育肥猪",  es: "Finalización",   vi: "Heo thịt" } },
  { id: "foster",    icon: Repeat,        color: "#0891B2", soft: "#ECFEFF", label: { en: "Foster",       ko: "양자",    zh: "寄养",   es: "Adopción",       vi: "Nuôi ghép" } },
];

const UI: Record<Locale, { title: string; sub: string }> = {
  en: { title: "Quick Input",    sub: "Select an event type" },
  ko: { title: "빠른 입력",       sub: "이벤트 유형을 선택하세요" },
  zh: { title: "快速录入",        sub: "选择事件类型" },
  es: { title: "Entrada Rápida", sub: "Selecciona el tipo de evento" },
  vi: { title: "Nhập nhanh",     sub: "Chọn loại sự kiện" },
};

export function QuickInputDrawer({ open, onClose, lang = "ko" }: QuickInputDrawerProps) {
  const router = useRouter();
  const [, setSelected] = useState<string | null>(null);

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

  const { title, sub } = UI[lang] ?? UI.en;

  if (!open) return null;

  return (
    <>
      <div
        className="fixed inset-0 bg-black/30 z-[90] backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="fixed bottom-0 left-0 right-0 md:bottom-auto md:left-1/2 md:top-1/2 md:-translate-x-1/2 md:-translate-y-1/2 md:w-[480px] z-[100] bg-surface rounded-t-2xl md:rounded-2xl shadow-2xl border border-border">
        <div className="flex justify-center pt-3 pb-1 md:hidden">
          <div className="w-10 h-1 bg-border rounded-full" />
        </div>

        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div>
            <h2 className="text-base font-bold text-text">{title}</h2>
            <p className="text-xs text-muted mt-0.5">{sub}</p>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-full bg-bg2 flex items-center justify-center text-muted hover:text-text transition"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="grid grid-cols-4 gap-3 p-5">
          {EVENTS.map((ev) => {
            const Icon = ev.icon;
            return (
              <button
                key={ev.id}
                onClick={() => handleSelect(ev.id)}
                className="flex flex-col items-center gap-2 p-3 rounded-xl border border-border hover:border-primary transition group"
                style={{ background: ev.soft }}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ background: ev.color + "18" }}
                >
                  <Icon className="w-5 h-5" style={{ color: ev.color }} />
                </div>
                <span className="text-[11px] font-semibold text-text2 text-center leading-tight">
                  {ev.label[lang]}
                </span>
              </button>
            );
          })}
        </div>

        <div className="pb-6 md:pb-4" />
      </div>
    </>
  );
}

"use client";

import { useState } from "react";
import Image from "next/image";
import {
  BrainCircuit,
  ListChecks,
  Package,
  Thermometer,
  FileSpreadsheet,
  Link2,
  QrCode,
  TrendingUp,
  ArrowRight,
  type LucideIcon,
} from "lucide-react";

type Category = "all" | "analytics" | "ops" | "iot" | "integration";

interface AddonCard {
  icon: LucideIcon;
  iconBg: string;
  iconColor: string;
  name: { ko: string; en: string };
  desc: { ko: string; en: string };
  tag: "coming_soon" | "beta" | "free";
  category: Exclude<Category, "all">;
}

const ADDONS: AddonCard[] = [
  {
    icon: BrainCircuit,
    iconBg: "bg-violet-50",
    iconColor: "text-violet-600",
    name: { ko: "AI 인사이트", en: "AI Insight" },
    desc: { ko: "KPI 이상 징후를 자연어로 설명하고 조치를 제안합니다", en: "Natural-language KPI analysis powered by Claude" },
    tag: "beta",
    category: "analytics",
  },
  {
    icon: ListChecks,
    iconBg: "bg-blue-50",
    iconColor: "text-blue-600",
    name: { ko: "Task 자동배정", en: "Auto Task Assign" },
    desc: { ko: "알림 발생 시 담당자에게 작업을 자동 생성하고 모바일로 전달합니다", en: "Auto-create tasks from alerts and push to staff mobile" },
    tag: "coming_soon",
    category: "ops",
  },
  {
    icon: Package,
    iconBg: "bg-amber-50",
    iconColor: "text-amber-600",
    name: { ko: "사료 재고 관리", en: "Feed Inventory" },
    desc: { ko: "입출고·재고 현황을 추적하고 FCR을 자동 계산합니다", en: "Feed in/out tracking with auto FCR calculation" },
    tag: "coming_soon",
    category: "ops",
  },
  {
    icon: Thermometer,
    iconBg: "bg-rose-50",
    iconColor: "text-rose-500",
    name: { ko: "IoT 환경 모니터링", en: "IoT Sensor" },
    desc: { ko: "온도·습도·암모니아를 실시간 수집하고 임계치 초과 시 알립니다", en: "Real-time barn environment via TimescaleDB" },
    tag: "coming_soon",
    category: "iot",
  },
  {
    icon: FileSpreadsheet,
    iconBg: "bg-emerald-50",
    iconColor: "text-emerald-600",
    name: { ko: "Excel/PDF 리포트", en: "Excel/PDF Export" },
    desc: { ko: "월간 성적 보고서를 자동 생성하고 다운로드합니다", en: "Auto-generate monthly performance reports" },
    tag: "coming_soon",
    category: "analytics",
  },
  {
    icon: Link2,
    iconBg: "bg-cyan-50",
    iconColor: "text-cyan-600",
    name: { ko: "도축장 연동", en: "Slaughterhouse Link" },
    desc: { ko: "출하 데이터를 도체 성적과 자동 매핑해 이력을 완성합니다", en: "Link shipment data to carcass grades for traceability" },
    tag: "coming_soon",
    category: "integration",
  },
  {
    icon: QrCode,
    iconBg: "bg-slate-100",
    iconColor: "text-slate-600",
    name: { ko: "QR 소비자 투명성", en: "QR Transparency" },
    desc: { ko: "소비자가 QR 스캔으로 농장 사육 이력을 확인합니다", en: "Consumer QR scan shows farm history — B2B premium" },
    tag: "coming_soon",
    category: "integration",
  },
  {
    icon: TrendingUp,
    iconBg: "bg-green-50",
    iconColor: "text-green-600",
    name: { ko: "데이터 배당", en: "Data Dividend" },
    desc: { ko: "익명 벤치마크 데이터 기여분에 따라 수익을 배분받습니다", en: "Contribute anonymized benchmarks, earn revenue share" },
    tag: "coming_soon",
    category: "analytics",
  },
];

const CATEGORIES: { value: Category; label: string }[] = [
  { value: "all",         label: "전체" },
  { value: "analytics",   label: "분석" },
  { value: "ops",         label: "운영" },
  { value: "iot",         label: "IoT" },
  { value: "integration", label: "연동" },
];

const TAG_STYLE: Record<AddonCard["tag"], string> = {
  free:        "bg-green-50 text-green-700 border-green-200",
  beta:        "bg-blue-50 text-blue-600 border-blue-200",
  coming_soon: "bg-bg2 text-text3 border-border",
};

const TAG_LABEL: Record<AddonCard["tag"], string> = {
  free:        "무료",
  beta:        "Beta",
  coming_soon: "출시 예정",
};

export default function AddonsPage() {
  const [category, setCategory] = useState<Category>("all");

  const filtered = category === "all" ? ADDONS : ADDONS.filter((a) => a.category === category);
  const betaCount = ADDONS.filter((a) => a.tag !== "coming_soon").length;

  return (
    <div className="p-7 max-w-5xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-[22px] font-extrabold tracking-tight text-text">Addon 스토어</h1>
        <p className="text-[13px] text-text3 mt-1">
          필요한 기능만 켜서 쓰는 PigOS 확장 모듈 · 현재 {betaCount}개 사용 가능, {ADDONS.length - betaCount}개 준비 중
        </p>
      </div>

      {/* Data Dividend hero */}
      <div className="relative rounded-2xl overflow-hidden mb-8 bg-[#0D1B3E]">
        {/* Watermark symbol */}
        <div className="absolute -right-10 -bottom-16 w-[260px] h-[260px] opacity-[0.07] pointer-events-none select-none">
          <Image src="/logos/pigos-symbol-dark.svg" alt="" fill className="object-contain" />
        </div>
        <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-[#FF5A66] via-[#2563EB] to-transparent" />

        <div className="relative z-10 px-7 py-7 lg:flex lg:items-center lg:justify-between lg:gap-10">
          <div className="max-w-md">
            <p className="text-[11px] font-bold tracking-[0.18em] uppercase text-[#FF5A66] mb-2.5">
              Data Dividend Program
            </p>
            <h2 className="text-white text-lg font-bold leading-snug">
              농장의 데이터가 농장의 수익이 됩니다
            </h2>
            <p className="text-slate-400 text-[13px] leading-relaxed mt-2">
              PigOS는 익명화된 벤치마크 데이터로 수익을 만들고, 기여한 농장에
              그 일부를 돌려드립니다. 모든 Addon은 무료로 시작합니다.
            </p>
            <button className="mt-4 inline-flex items-center gap-1.5 text-[13px] font-semibold text-white/90 hover:text-white transition group">
              프로그램 자세히 보기
              <ArrowRight size={14} className="transition-transform group-hover:translate-x-0.5" />
            </button>
          </div>

          {/* How it works — quiet 3-step */}
          <div className="hidden lg:block flex-shrink-0 w-[260px]">
            <div className="space-y-0">
              {[
                { n: "01", title: "Addon 무료 사용", sub: "기능을 켜는 순간 데이터가 쌓입니다" },
                { n: "02", title: "익명 벤치마크 기여", sub: "농장 식별 정보는 제거됩니다" },
                { n: "03", title: "분기별 수익 배분", sub: "기여도에 비례해 정산됩니다" },
              ].map((s, i, arr) => (
                <div key={s.n} className="flex gap-3.5">
                  <div className="flex flex-col items-center">
                    <span className="font-mono text-[10px] text-slate-500 w-7 h-7 rounded-full border border-white/15 flex items-center justify-center flex-shrink-0">
                      {s.n}
                    </span>
                    {i < arr.length - 1 && <div className="w-px flex-1 bg-white/10 my-1" />}
                  </div>
                  <div className={i < arr.length - 1 ? "pb-4" : ""}>
                    <div className="text-[13px] font-semibold text-white/90 leading-7">{s.title}</div>
                    <div className="text-[11px] text-slate-500 -mt-0.5">{s.sub}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Category filter */}
      <div className="flex items-center gap-1.5 mb-5">
        {CATEGORIES.map((c) => (
          <button
            key={c.value}
            onClick={() => setCategory(c.value)}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition border ${
              category === c.value
                ? "bg-navy text-white border-navy"
                : "bg-surface text-text3 border-border hover:text-text hover:border-text3/40"
            }`}
          >
            {c.label}
          </button>
        ))}
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {filtered.map((addon) => {
          const Icon = addon.icon;
          const disabled = addon.tag === "coming_soon";
          return (
            <div
              key={addon.name.en}
              className={`group bg-surface border border-border rounded-2xl p-5 flex flex-col gap-3.5 transition ${
                disabled ? "" : "hover:border-primary/40 hover:shadow-sm"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className={`w-10 h-10 rounded-xl ${addon.iconBg} flex items-center justify-center`}>
                  <Icon size={19} className={addon.iconColor} strokeWidth={1.8} />
                </div>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${TAG_STYLE[addon.tag]}`}>
                  {TAG_LABEL[addon.tag]}
                </span>
              </div>
              <div className="flex-1">
                <div className="font-bold text-[14px] text-text">{addon.name.ko}</div>
                <div className="text-xs text-text3 mt-1 leading-relaxed">{addon.desc.ko}</div>
              </div>
              <button
                disabled={disabled}
                className={`text-xs font-semibold rounded-lg px-3 py-2 transition ${
                  disabled
                    ? "bg-bg2 text-text3/60 cursor-default"
                    : "bg-primary text-white hover:bg-blue-700"
                }`}
              >
                {disabled ? "출시 예정" : addon.tag === "beta" ? "Beta 시작하기" : "무료 활성화"}
              </button>
            </div>
          );
        })}
      </div>

      {/* Request */}
      <div className="mt-8 border border-dashed border-border rounded-2xl px-6 py-5 flex items-center justify-between gap-4">
        <div>
          <div className="text-sm font-bold text-text">찾는 기능이 없나요?</div>
          <div className="text-xs text-text3 mt-0.5">필요한 Addon을 제안해 주시면 로드맵에 반영합니다</div>
        </div>
        <a
          href="/support"
          className="flex-shrink-0 text-xs font-semibold text-primary border border-primary/30 rounded-lg px-4 py-2 hover:bg-primary/5 transition"
        >
          Addon 제안하기
        </a>
      </div>
    </div>
  );
}

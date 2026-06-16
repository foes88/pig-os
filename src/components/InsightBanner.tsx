"use client";

import { useTranslations } from "next-intl";
import { AlertTriangle, AlertOctagon, Info, Globe } from "lucide-react";
import type { EventInsight } from "@/types/api.types";

/**
 * 이벤트 입력 즉시 분석 배너 — **순수 렌더러**.
 * 판정(severity)은 백엔드 Rule Engine이 한다. 이 컴포넌트는 EventInsight[]를 받아 표시만.
 * - normal(INFO)은 작게, WARNING/CRITICAL만 강하게.
 * - 출처/신뢰도/proxy 배지 표시.
 * - loss/relative 슬롯은 데이터 있을 때만 조건부 표시(지금은 항상 없음).
 */
export function InsightBanner({ insights }: { insights?: EventInsight[] }) {
  const t = useTranslations("insights");
  if (!insights || insights.length === 0) return null;

  // 백엔드가 준 severity로만 정렬(프론트 판정 아님): CRITICAL > WARNING > INFO
  const rank: Record<string, number> = { CRITICAL: 0, WARNING: 1, INFO: 2 };
  const sorted = [...insights].sort((a, b) => (rank[a.severity] ?? 9) - (rank[b.severity] ?? 9));

  return (
    <div className="mt-3 space-y-2">
      {sorted.map((ins, i) => (
        <InsightRow key={`${ins.metric_code}-${i}`} ins={ins} t={t} />
      ))}
    </div>
  );
}

const STYLE: Record<string, { box: string; icon: typeof Info; iconCls: string }> = {
  CRITICAL: { box: "bg-red-50 border-red-300",    icon: AlertOctagon,  iconCls: "text-danger" },
  WARNING:  { box: "bg-amber-50 border-amber-300", icon: AlertTriangle, iconCls: "text-warning" },
  INFO:     { box: "bg-slate-50 border-slate-200",  icon: Info,          iconCls: "text-text3" },
};

function InsightRow({ ins, t }: { ins: EventInsight; t: ReturnType<typeof useTranslations> }) {
  const isStrong = ins.severity === "WARNING" || ins.severity === "CRITICAL";
  const s = STYLE[ins.severity] ?? STYLE.INFO;
  const Icon = s.icon;

  // 문구는 i18n 템플릿(metric+severity)에 값/임계 보간 — 판정이 아니라 표현
  const metricLabel = safe(t, `metric.${ins.metric_code}`, ins.metric_code);
  const title = safe(
    t, `msg.${ins.metric_code}.${ins.severity}`,
    safe(t, `msgGeneric.${ins.severity}`, metricLabel),
    { metric: metricLabel, value: fmt(ins.value), threshold: fmt(ins.threshold), unit: ins.unit },
  );
  const action = safe(t, `action.${ins.metric_code}`, "", {});

  // normal(INFO)은 한 줄 작게
  if (!isStrong) {
    return (
      <div className="flex items-center gap-2 text-[11px] text-text3 px-2 py-1">
        <Icon className="w-3 h-3 flex-shrink-0" />
        <span className="truncate">{title}</span>
        <Badges ins={ins} t={t} small />
      </div>
    );
  }

  // warning/critical 강하게
  return (
    <div className={`border rounded-xl px-3.5 py-3 ${s.box}`}>
      <div className="flex items-start gap-2.5">
        <Icon className={`w-4.5 h-4.5 mt-0.5 flex-shrink-0 ${s.iconCls}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-bold text-text">{title}</span>
            <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${ins.severity === "CRITICAL" ? "bg-danger text-white" : "bg-warning text-white"}`}>
              {t(`sev.${ins.severity}`)}
            </span>
          </div>
          {action && <p className="text-xs text-text2 mt-1">{action}</p>}
          <Badges ins={ins} t={t} />

          {/* 슬롯: 데이터 있을 때만 (지금은 항상 비어 표시 안 됨) */}
          {ins.relative && <RelativeSlot data={ins.relative} t={t} />}
          {ins.loss && <LossSlot data={ins.loss} t={t} />}
        </div>
      </div>
    </div>
  );
}

function Badges({ ins, t, small }: { ins: EventInsight; t: ReturnType<typeof useTranslations>; small?: boolean }) {
  const cls = `inline-flex items-center gap-0.5 ${small ? "text-[8px]" : "text-[9px]"} font-semibold px-1.5 py-0.5 rounded-full border`;
  return (
    <span className="inline-flex items-center gap-1 flex-wrap mt-0.5">
      {ins.is_global_fallback && (
        <span className={`${cls} border-blue-200 text-blue-600 bg-blue-50/50`}>
          <Globe className="w-2.5 h-2.5" />{t("badge.global")}
        </span>
      )}
      {ins.is_proxy && (
        <span className={`${cls} border-purple-200 text-purple-600 bg-purple-50/50`}>{t("badge.proxy")}</span>
      )}
      {ins.confidence && (
        <span className={`${cls} ${CONF_CLS[ins.confidence] ?? "border-border text-text3"}`}>
          {t(`badge.conf.${ins.confidence}`)}
        </span>
      )}
      {ins.source && (
        <span className={`${cls} border-border text-text3`} title={ins.source}>{ins.source}</span>
      )}
    </span>
  );
}

const CONF_CLS: Record<string, string> = {
  high: "border-green-200 text-green-600",
  medium: "border-amber-200 text-amber-600",
  low: "border-red-200 text-red-500",
};

// ── 슬롯 (추후 데이터 들어오면 채움. 가상수치면 Demo 배지) ───────────────────
function RelativeSlot({ data, t }: { data: Record<string, unknown>; t: ReturnType<typeof useTranslations> }) {
  const demo = (data as { demo?: boolean }).demo;
  return (
    <div className="mt-1.5 text-[11px] text-text3 border-t border-border/60 pt-1.5">
      {t("slot.relative")} {demo && <DemoBadge t={t} />}
    </div>
  );
}

function LossSlot({ data, t }: { data: Record<string, unknown>; t: ReturnType<typeof useTranslations> }) {
  const demo = (data as { demo?: boolean }).demo;
  return (
    <div className="mt-1 text-[11px] text-text3">
      {t("slot.loss")} {demo && <DemoBadge t={t} />}
    </div>
  );
}

function DemoBadge({ t }: { t: ReturnType<typeof useTranslations> }) {
  return <span className="text-[8px] font-bold px-1 py-0.5 rounded bg-slate-200 text-slate-600">{t("badge.demo")}</span>;
}

// i18n 키 없으면 fallback (next-intl은 키 없을 때 throw → 안전 래퍼)
function safe(
  t: ReturnType<typeof useTranslations>, key: string, fallback: string,
  vars?: Record<string, string>,
): string {
  try {
    return t(key, vars);
  } catch {
    return fallback;
  }
}

function fmt(n: number | null): string {
  return n == null ? "-" : String(n);
}

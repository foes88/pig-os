// AI 신호(룰엔진) 메타 — 08 신호목록 / 09 신호상세 공유.
// 심각도·감지규칙·임계·권장조치를 한 곳에서 관리(설명가능 AI의 근거).
// 모든 텍스트는 i18n 키로만 — 실제 문자열은 messages/*.json alertsMeta 네임스페이스.

import type { OverdueType } from "@/types/api.types";

export type Severity = "critical" | "warning" | "info";

export interface AlertMeta {
  /** 심각도 (좌측 색띠·탭 분류) */
  severity: Severity;
  /** i18n 라벨 키 (alerts 네임스페이스, 기존 재사용) */
  labelKey: string;
  /** 감지 규칙 설명 i18n 키 (alertsMeta) */
  ruleKey: string;
  /** 임계 일수 (farm_config 기본값) */
  threshold: number;
  /** record 입력 탭 */
  action: "mating" | "weaning";
  /** 권장 조치 i18n 키 배열 (alertsMeta) */
  actionKeys: string[];
}

export const ALERT_META: Record<OverdueType, AlertMeta> = {
  pregnant_overdue_farrowing: {
    severity: "critical",
    labelKey: "pregnantOverdueFarrowing",
    ruleKey: "rulePregnantOverdueFarrowing",
    threshold: 114,
    action: "mating",
    actionKeys: ["actPregCheck", "actVetReview", "actVerifyMating"],
  },
  open_overdue_mating: {
    severity: "critical",
    labelKey: "openOverdueMating",
    ruleKey: "ruleOpenOverdueMating",
    threshold: 7,
    action: "mating",
    actionKeys: ["actHeatCheck", "actBoarContact", "actHormoneReview"],
  },
  accident_overdue_mating: {
    severity: "warning",
    labelKey: "accidentOverdueMating",
    ruleKey: "ruleAccidentOverdueMating",
    threshold: 7,
    action: "mating",
    actionKeys: ["actHeatCheck", "actCullReview"],
  },
  lactating_overdue_weaning: {
    severity: "warning",
    labelKey: "lactatingOverdueWeaning",
    ruleKey: "ruleLactatingOverdueWeaning",
    threshold: 21,
    action: "weaning",
    actionKeys: ["actWeanNow", "actCheckLitter"],
  },
  gilt_overdue_mating: {
    severity: "warning",
    labelKey: "giltOverdueMating",
    ruleKey: "ruleGiltOverdueMating",
    threshold: 240,
    action: "mating",
    actionKeys: ["actHeatCheck", "actGiltStimulation", "actCullReview"],
  },
  gilt_no_estrus: {
    severity: "info",
    labelKey: "giltNoEstrus",
    ruleKey: "ruleGiltNoEstrus",
    threshold: 240,
    action: "mating",
    actionKeys: ["actHeatCheck", "actGiltStimulation"],
  },
};

export const SEVERITY_BAND: Record<Severity, string> = {
  critical: "bg-danger",
  warning: "bg-warning",
  info: "bg-success",
};

export const SEVERITY_PILL: Record<Severity, string> = {
  critical: "bg-red-soft text-danger border-danger/40",
  warning: "bg-amber-soft text-warning border-warning/40",
  info: "bg-green-soft text-success border-success/30",
};

export const ALL_OVERDUE_TYPES = Object.keys(ALERT_META) as OverdueType[];

// KPI 상태 4단계 판정 + 유효범위 검증. (severity enum 고정: normal|warning|critical|insufficient)
// normal=목표달성 / warning=주의 / critical=위험 / insufficient=데이터부족(null·NaN·범위밖)
// good/danger 금지 — normal/critical 사용.

export type KpiTier = "normal" | "warning" | "critical" | "insufficient";

function invalid(v: number | null | undefined, min: number, max: number): boolean {
  return v == null || !Number.isFinite(v) || v < min || v > max;
}

/** PSY 유효 0~45. ≥28 normal / ≥22 warning / 그외 critical. */
export function psyTier(v: number | null | undefined): KpiTier {
  if (invalid(v, 0, 45)) return "insufficient";
  const n = v as number;
  return n >= 28 ? "normal" : n >= 22 ? "warning" : "critical";
}

/** NPD 유효 0~365. ≤35 normal / ≤50 warning / 그외 critical. */
export function npdTier(v: number | null | undefined): KpiTier {
  if (invalid(v, 0, 365)) return "insufficient";
  const n = v as number;
  return n <= 35 ? "normal" : n <= 50 ? "warning" : "critical";
}

/** 분만율 — percent(0~100) 단일 SSOT(2026-06-25, 시드 benchmarks와 동일 스케일). ≥90 normal / ≥80 warning / 그외 critical. */
export function farrowingRateTier(v: number | null | undefined): KpiTier {
  if (invalid(v, 0, 100)) return "insufficient";
  const n = v as number;
  return n >= 90 ? "normal" : n >= 80 ? "warning" : "critical";
}

/** tier → 색상 토큰. 색의미: normal=outline(white카드 내), warning/critical=fill accent, insufficient=brown. */
export const TIER_STYLE: Record<KpiTier, { text: string; dot: string; chip: string }> = {
  normal:       { text: "text-success", dot: "bg-success", chip: "bg-transparent text-success border-success" },
  warning:      { text: "text-warning", dot: "bg-warning", chip: "bg-amber-soft text-warning border-warning/40" },
  critical:     { text: "text-danger",  dot: "bg-danger",  chip: "bg-red-soft text-danger border-danger/40" },
  insufficient: { text: "text-insufficient", dot: "bg-insufficient", chip: "bg-insufficient-soft text-insufficient border-insufficient-border" },
};

/** kpi_code → legacy 판정 함수. ADR-KPI-08 Phase 3 폴백 전용(백엔드 kpi_status 부재 시).
 *  ★ 새 임계값을 여기 추가하지 말 것 — 판정은 백엔드 국가정책 소관.
 *  Phase 4(백엔드 status 전면 적용)에서 이 맵과 위 함수들을 함께 제거한다. */
export const LEGACY_TIER_FN: Record<string, (v: number | null | undefined) => KpiTier> = {
  PSY: psyTier,
  NPD: npdTier,
  FARROWING_RATE: farrowingRateTier,
};

/** 레지스트리에 legacy 판정이 없는 KPI(SOW_TURNOVER 등)는 프론트가 판정하지 않는다. */
export function legacyTier(kpiCode: string, v: number | null | undefined): KpiTier {
  const fn = LEGACY_TIER_FN[kpiCode];
  return fn ? fn(v) : "normal";
}

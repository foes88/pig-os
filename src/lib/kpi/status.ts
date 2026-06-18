// KPI 상태 4단계 판정 + 유효범위 검증.
// good=목표달성 / warning=주의 / critical=위험 / insufficient=데이터부족(null·NaN·범위밖)

export type KpiTier = "good" | "warning" | "critical" | "insufficient";

function invalid(v: number | null | undefined, min: number, max: number): boolean {
  return v == null || !Number.isFinite(v) || v < min || v > max;
}

/** PSY 유효 0~45. ≥28 good / ≥22 warning / 그외 critical. */
export function psyTier(v: number | null | undefined): KpiTier {
  if (invalid(v, 0, 45)) return "insufficient";
  const n = v as number;
  return n >= 28 ? "good" : n >= 22 ? "warning" : "critical";
}

/** NPD 유효 0~365. ≤35 good / ≤50 warning / 그외 critical. */
export function npdTier(v: number | null | undefined): KpiTier {
  if (invalid(v, 0, 365)) return "insufficient";
  const n = v as number;
  return n <= 35 ? "good" : n <= 50 ? "warning" : "critical";
}

/** 분만율 — 비율(0~1)로 받음. 범위 밖(예: 34.78=3478%)이면 데이터부족. ≥0.9 good / ≥0.8 warning / 그외 critical. */
export function farrowingRateTier(v: number | null | undefined): KpiTier {
  if (invalid(v, 0, 1)) return "insufficient";
  const n = v as number;
  return n >= 0.9 ? "good" : n >= 0.8 ? "warning" : "critical";
}

/** tier → 색상 토큰(텍스트/배경). */
export const TIER_STYLE: Record<KpiTier, { text: string; dot: string; chip: string }> = {
  good:         { text: "text-success", dot: "bg-success", chip: "bg-green-50 text-success border-green-200" },
  warning:      { text: "text-warning", dot: "bg-warning", chip: "bg-amber-50 text-warning border-amber-200" },
  critical:     { text: "text-danger",  dot: "bg-danger",  chip: "bg-red-50 text-danger border-red-200" },
  insufficient: { text: "text-text3",   dot: "bg-text3",   chip: "bg-bg2 text-text3 border-border" },
};

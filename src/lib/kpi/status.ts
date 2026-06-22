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

/** 분만율 — 비율(0~1). 범위 밖(예: 34.78=3478%)이면 데이터부족. ≥0.9 normal / ≥0.8 warning / 그외 critical. */
export function farrowingRateTier(v: number | null | undefined): KpiTier {
  if (invalid(v, 0, 1)) return "insufficient";
  const n = v as number;
  return n >= 0.9 ? "normal" : n >= 0.8 ? "warning" : "critical";
}

/** tier → 색상 토큰. 색의미: normal=outline(white카드 내), warning/critical=fill accent, insufficient=brown. */
export const TIER_STYLE: Record<KpiTier, { text: string; dot: string; chip: string }> = {
  normal:       { text: "text-success", dot: "bg-success", chip: "bg-transparent text-success border-success" },
  warning:      { text: "text-warning", dot: "bg-warning", chip: "bg-amber-soft text-warning border-warning/40" },
  critical:     { text: "text-danger",  dot: "bg-danger",  chip: "bg-red-soft text-danger border-danger/40" },
  insufficient: { text: "text-insufficient", dot: "bg-insufficient", chip: "bg-insufficient-soft text-insufficient border-insufficient-border" },
};

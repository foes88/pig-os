import type { KpiTrend } from "@/types/api.types";

/** 1자리 고정 포맷(화면 테이블과 동일). null/undefined → 빈 문자열. */
export function fmt1(v: number | null | undefined): string {
  return v != null ? v.toFixed(1) : "";
}

/**
 * 번식 추세 CSV 행(헤더 제외). 화면 테이블과 동일하게 period + PSY/NPD/FR 3개 KPI를
 * 모두 포함(H2: 단일 KPI만 내보내던 버그 수정). 헤더는 i18n이라 호출부에서 결합.
 */
export function buildReproCsvRows(trend: KpiTrend[]): string[][] {
  return trend.map((r) => [r.period, fmt1(r.psy), fmt1(r.npd), fmt1(r.farrowing_rate)]);
}

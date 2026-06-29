import { describe, it, expect } from "vitest";

import { fmt1, buildReproCsvRows } from "@/lib/reports/csv";
import type { KpiTrend } from "@/types/api.types";

describe("reports CSV (H2: 화면 테이블과 동일하게 3 KPI 전부)", () => {
  it("fmt1: 1자리 고정, null/undefined는 빈 문자열", () => {
    expect(fmt1(27.319)).toBe("27.3");
    expect(fmt1(0)).toBe("0.0");
    expect(fmt1(null)).toBe("");
    expect(fmt1(undefined)).toBe("");
  });

  it("buildReproCsvRows: period + PSY/NPD/FR 4열을 행마다 생성", () => {
    const trend = [
      { period: "2026-01", psy: 28.12, npd: 35.4, farrowing_rate: 86.0 },
      { period: "2026-02", psy: null, npd: 36, farrowing_rate: null },
    ] as unknown as KpiTrend[];
    const rows = buildReproCsvRows(trend);
    expect(rows).toEqual([
      ["2026-01", "28.1", "35.4", "86.0"],
      ["2026-02", "", "36.0", ""],
    ]);
    // 단일 KPI(2열)만 내보내던 회귀 방지 — 항상 4열.
    expect(rows.every((r) => r.length === 4)).toBe(true);
  });

  it("빈 추세 → 빈 행", () => {
    expect(buildReproCsvRows([])).toEqual([]);
  });
});

import { describe, it, expect } from "vitest";
import { psyTier, npdTier, farrowingRateTier } from "@/lib/kpi/status";

// KPI tier 경계값 고정 — 임계 변경 시 회귀 감지(순수함수, mock 불필요).

describe("psyTier (≥28 normal · ≥22 warning · else critical, 유효 0~45)", () => {
  it("경계값", () => {
    expect(psyTier(28)).toBe("normal");
    expect(psyTier(27.9)).toBe("warning");
    expect(psyTier(22)).toBe("warning");
    expect(psyTier(21.9)).toBe("critical");
    expect(psyTier(0)).toBe("critical");
    expect(psyTier(45)).toBe("normal"); // 45=유효상한, 28↑이므로 normal
  });
  it("무효 → insufficient", () => {
    for (const v of [null, undefined, NaN, -1, 45.1, Infinity]) {
      expect(psyTier(v as number)).toBe("insufficient");
    }
  });
});

describe("npdTier (≤35 normal · ≤50 warning · else critical, 유효 0~365)", () => {
  it("경계값", () => {
    expect(npdTier(35)).toBe("normal");
    expect(npdTier(35.1)).toBe("warning");
    expect(npdTier(50)).toBe("warning");
    expect(npdTier(50.1)).toBe("critical");
    expect(npdTier(0)).toBe("normal");
  });
  it("무효 → insufficient", () => {
    for (const v of [null, undefined, NaN, -1, 365.1]) {
      expect(npdTier(v as number)).toBe("insufficient");
    }
  });
});

describe("farrowingRateTier (≥90 normal · ≥80 warning · else critical, 유효 0~100)", () => {
  it("경계값", () => {
    expect(farrowingRateTier(90)).toBe("normal");
    expect(farrowingRateTier(89.9)).toBe("warning");
    expect(farrowingRateTier(80)).toBe("warning");
    expect(farrowingRateTier(79.9)).toBe("critical");
    expect(farrowingRateTier(100)).toBe("normal");
  });
  it("무효 → insufficient", () => {
    for (const v of [null, undefined, NaN, -1, 100.1]) {
      expect(farrowingRateTier(v as number)).toBe("insufficient");
    }
  });
});

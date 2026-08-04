import { describe, it, expect } from "vitest";
import {
  kgToDisplay,
  lbToKg,
  formatWeight,
  formatCurrency,
  celsiusToDisplay,
} from "@/lib/utils/units";

// 단위 변환·표시 포맷 고정 — DB는 metric 저장, 표시 변환만 여기서.

describe("kgToDisplay", () => {
  it("kg 단위는 그대로, lb는 환산+소수1자리", () => {
    expect(kgToDisplay(100, "kg")).toBe(100);
    expect(kgToDisplay(100, "lb")).toBe(220.5); // 100*2.20462=220.462 → 220.5
    expect(kgToDisplay(0, "lb")).toBe(0);
  });
  it("null/undefined → null", () => {
    expect(kgToDisplay(null, "lb")).toBeNull();
    expect(kgToDisplay(undefined, "kg")).toBeNull();
  });
});

describe("lbToKg", () => {
  it("역환산 소수1자리 반올림", () => {
    expect(lbToKg(220.462)).toBe(100);
    expect(lbToKg(2.20462)).toBe(1);
  });
});

describe("formatWeight", () => {
  it("값+단위 문자열", () => {
    expect(formatWeight(100, "kg")).toBe("100.0 kg");
    expect(formatWeight(100, "lb")).toBe("220.5 lb");
    expect(formatWeight(50, "kg", 0)).toBe("50 kg");
  });
  it("null → '-'", () => {
    expect(formatWeight(null, "kg")).toBe("-");
  });
});

describe("formatCurrency", () => {
  it("천단위 구분 + 심볼", () => {
    expect(formatCurrency(12345, "$")).toBe("$12,345");
    expect(formatCurrency(1000, "₩")).toBe("₩1,000");
    expect(formatCurrency(1234.56, "$", 2)).toBe("$1,234.56");
  });
  it("null → '-'", () => {
    expect(formatCurrency(null, "$")).toBe("-");
  });
});

describe("celsiusToDisplay", () => {
  it("NA 시장은 °F, 그 외 °C", () => {
    expect(celsiusToDisplay(20, "NA")).toBe("68.0°F");
    expect(celsiusToDisplay(20, "KR")).toBe("20.0°C");
    expect(celsiusToDisplay(0, "NA")).toBe("32.0°F");
  });
  it("null → '-'", () => {
    expect(celsiusToDisplay(null, "NA")).toBe("-");
  });
});

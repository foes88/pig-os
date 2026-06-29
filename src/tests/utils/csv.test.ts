import { describe, it, expect } from "vitest";

import { escapeCsvCell, toCsv } from "@/lib/utils/csv";

describe("toCsv (reports CSV export)", () => {
  it("joins headers and rows with commas/newlines", () => {
    const out = toCsv(["period", "psy"], [["2026-01", 28], ["2026-02", 30]]);
    expect(out).toBe("period,psy\n2026-01,28\n2026-02,30");
  });

  it("renders null/undefined cells as empty", () => {
    const out = toCsv(["a", "b"], [[null, 1]]);
    expect(out).toBe("a,b\n,1");
  });

  it("handles header-only (no rows)", () => {
    expect(toCsv(["x", "y"], [])).toBe("x,y");
  });

  it("quotes cells containing comma/quote/newline (no field shifting)", () => {
    // 품종명 'Duroc, F1'이 콤마로 컬럼을 밀던 버그 차단
    const out = toCsv(["breed", "psy"], [["Duroc, F1", 28], ['He said "hi"', 1]]);
    expect(out).toBe('breed,psy\n"Duroc, F1",28\n"He said ""hi""",1');
  });

  it("neutralizes formula injection in string cells (=,+,-,@ leading)", () => {
    expect(escapeCsvCell("=WEBSERVICE(1)")).toBe("'=WEBSERVICE(1)");
    expect(escapeCsvCell("+1+2")).toBe("'+1+2");
    expect(escapeCsvCell("@SUM(A1)")).toBe("'@SUM(A1)");
    expect(escapeCsvCell("-cmd")).toBe("'-cmd");
  });

  it("does not prefix numeric negatives (numbers are safe)", () => {
    expect(escapeCsvCell(-5)).toBe("-5");
  });

  it("combines formula-prefix and quoting when needed", () => {
    expect(escapeCsvCell("=A1,B1")).toBe('"\'=A1,B1"');
  });
});

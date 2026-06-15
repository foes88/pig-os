import { describe, it, expect } from "vitest";

import { toCsv } from "@/lib/utils/csv";

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
});

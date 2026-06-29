import { describe, it, expect } from "vitest";

import { canEntry, canManage, canOwn } from "@/lib/auth/permissions";

// 백엔드 require_farm_role 티어와 1:1 일치해야 함(프론트 버튼 노출 = 백엔드 허용).
// ENTRY = OWNER/MANAGER/WORKER, MANAGE = OWNER/MANAGER, OWN = OWNER (+ SUPER_ADMIN).
describe("permission gating matrix", () => {
  it("canEntry: OWNER/MANAGER/WORKER 허용, VIEWER/VET 거부", () => {
    for (const r of ["FARM_OWNER", "FARM_MANAGER", "FARM_WORKER", "SUPER_ADMIN"]) {
      expect(canEntry(r)).toBe(true);
    }
    for (const r of ["VIEWER", "VET"]) expect(canEntry(r)).toBe(false);
  });

  it("canManage: OWNER/MANAGER 허용, WORKER/VIEWER/VET 거부 (도태·feed삭제 등)", () => {
    for (const r of ["FARM_OWNER", "FARM_MANAGER", "SUPER_ADMIN"]) {
      expect(canManage(r)).toBe(true);
    }
    for (const r of ["FARM_WORKER", "VIEWER", "VET"]) expect(canManage(r)).toBe(false);
  });

  it("canOwn: OWNER만(+SUPER_ADMIN), MANAGER 이하 거부 (멤버임명·과금·삭제)", () => {
    expect(canOwn("FARM_OWNER")).toBe(true);
    expect(canOwn("SUPER_ADMIN")).toBe(true);
    for (const r of ["FARM_MANAGER", "FARM_WORKER", "VIEWER", "VET"]) {
      expect(canOwn(r)).toBe(false);
    }
  });

  it("null/undefined/빈 role은 모두 거부", () => {
    for (const fn of [canEntry, canManage, canOwn]) {
      expect(fn(null)).toBe(false);
      expect(fn(undefined)).toBe(false);
      expect(fn("")).toBe(false);
    }
  });
});

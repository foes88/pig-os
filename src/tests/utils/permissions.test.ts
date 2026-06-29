import { describe, it, expect } from "vitest";

import { canEntry, canManage, canOwn, effectiveRole } from "@/lib/auth/permissions";

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

describe("effectiveRole (멀티팜 활성농장 역할)", () => {
  it("활성 농장의 farm_roles를 우선 사용", () => {
    const user = { role: "FARM_WORKER", farm_roles: { f1: "FARM_OWNER", f2: "VIEWER" } };
    expect(effectiveRole(user, "f1")).toBe("FARM_OWNER");
    expect(effectiveRole(user, "f2")).toBe("VIEWER");
  });

  it("farm_roles에 없는 농장이면 전역 role로 폴백", () => {
    const user = { role: "FARM_MANAGER", farm_roles: { f1: "FARM_OWNER" } };
    expect(effectiveRole(user, "f9")).toBe("FARM_MANAGER");
  });

  it("farm_roles 없음(SUPER_ADMIN·단일농장)이면 전역 role", () => {
    expect(effectiveRole({ role: "SUPER_ADMIN" }, "f1")).toBe("SUPER_ADMIN");
    expect(effectiveRole({ role: "FARM_OWNER", farm_roles: {} }, "f1")).toBe("FARM_OWNER");
  });

  it("user 없으면 null", () => {
    expect(effectiveRole(null, "f1")).toBeNull();
    expect(effectiveRole(undefined, null)).toBeNull();
  });

  it("같은 사용자라도 농장 전환 시 권한이 바뀐다(핵심 시나리오)", () => {
    const user = { role: "VIEWER", farm_roles: { fa: "FARM_OWNER", fb: "FARM_WORKER" } };
    // 농장 A에서는 소유자 → 관리 가능
    expect(canManage(effectiveRole(user, "fa"))).toBe(true);
    // 농장 B에서는 작업자 → 관리 불가, 입력만 가능
    expect(canManage(effectiveRole(user, "fb"))).toBe(false);
    expect(canEntry(effectiveRole(user, "fb"))).toBe(true);
  });
});

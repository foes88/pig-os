import { describe, it, expect } from "vitest";
import { ADMIN_NAV } from "@/lib/admin/nav";

// 운영자 어드민 메뉴 레지스트리 불변식 — 항목 추가 시 형식 회귀 방지.

describe("ADMIN_NAV 레지스트리", () => {
  it("항목이 하나 이상", () => {
    expect(ADMIN_NAV.length).toBeGreaterThan(0);
  });

  it("각 항목: href·labelKey·icon·유효 status", () => {
    for (const item of ADMIN_NAV) {
      expect(item.href.startsWith("/admin")).toBe(true);
      expect(item.labelKey.length).toBeGreaterThan(0);
      expect(item.icon).toBeTruthy();
      expect(["ready", "soon"]).toContain(item.status);
    }
  });

  it("href 중복 없음", () => {
    const hrefs = ADMIN_NAV.map((i) => i.href);
    expect(new Set(hrefs).size).toBe(hrefs.length);
  });

  it("labelKey 중복 없음", () => {
    const keys = ADMIN_NAV.map((i) => i.labelKey);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it("개요(/admin) 진입점 존재", () => {
    expect(ADMIN_NAV.some((i) => i.href === "/admin")).toBe(true);
  });
});

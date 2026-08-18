import { describe, it, expect, vi, beforeEach } from "vitest";
import { findStatusMismatches, reportStatusMismatches, resolveTier } from "@/lib/kpi/statusObservation";
import type { KpiStatusDto } from "@/types/api.types";

vi.mock("@/lib/analytics", () => ({ track: vi.fn() }));
import { track } from "@/lib/analytics";

const be = (status: string, reason: string | null = null): KpiStatusDto =>
  ({ status, reason } as KpiStatusDto);

describe("findStatusMismatches (ADR-KPI-08 Phase 2 관측)", () => {
  beforeEach(() => vi.mocked(track).mockClear());

  it("동일 판정이면 불일치 없음", () => {
    const out = findStatusMismatches({ PSY: be("normal") }, { PSY: "normal" });
    expect(out).toEqual([]);
  });

  it("백엔드 warning · 프론트 normal → 놓친 경보로 검출", () => {
    const out = findStatusMismatches({ PSY: be("warning") }, { PSY: "normal" });
    expect(out).toHaveLength(1);
    expect(out[0]).toMatchObject({ metric: "PSY", backend: "warning", frontend: "normal" });
  });

  it("백엔드 insufficient도 불일치로 본다(프론트가 임의 판정 중)", () => {
    const out = findStatusMismatches(
      { NPD: be("insufficient", "policy_pending") },
      { NPD: "normal" },
    );
    expect(out[0]).toMatchObject({ backend: "insufficient", backendReason: "policy_pending" });
  });

  it("백엔드가 주지 않은 지표는 비교 대상 아님", () => {
    const out = findStatusMismatches({}, { PSY: "critical" });
    expect(out).toEqual([]);
  });

  it("kpi_status 미제공(구버전 API)이면 빈 배열 — 안전", () => {
    expect(findStatusMismatches(undefined, { PSY: "normal" })).toEqual([]);
  });
});

describe("resolveTier (Phase 3 — 백엔드 판정 우선)", () => {
  it("백엔드 status가 있으면 그것을 쓴다(국가별 정책 반영)", () => {
    // legacy는 warning이지만 백엔드(US 기준)는 normal → 백엔드 승
    expect(resolveTier({ PSY: be("normal") }, "PSY", "warning")).toBe("normal");
    expect(resolveTier({ NPD: be("critical") }, "NPD", "normal")).toBe("critical");
  });

  it("백엔드가 status를 안 주면 legacy 폴백(구버전 API 안전)", () => {
    expect(resolveTier(undefined, "PSY", "warning")).toBe("warning");
    expect(resolveTier({}, "PSY", "critical")).toBe("critical");
  });

  it("insufficient도 그대로 반영(프론트가 임의 판정하지 않음)", () => {
    expect(resolveTier({ SOW_TURNOVER: be("insufficient", "no_policy") }, "SOW_TURNOVER", "normal"))
      .toBe("insufficient");
  });

  it("미지의 status는 중립(insufficient) — 임계 계산으로 되돌아가지 않음", () => {
    expect(resolveTier({ PSY: be("excellent") }, "PSY", "normal")).toBe("insufficient");
  });

  it("대소문자 무관", () => {
    expect(resolveTier({ PSY: be("WARNING") }, "PSY", "normal")).toBe("warning");
  });
});

describe("reportStatusMismatches", () => {
  beforeEach(() => vi.mocked(track).mockClear());

  it("불일치가 있을 때만 track 호출", () => {
    reportStatusMismatches({ PSY: be("normal") }, { PSY: "normal" });
    expect(track).not.toHaveBeenCalled();

    reportStatusMismatches({ PSY: be("critical") }, { PSY: "normal" });
    expect(track).toHaveBeenCalledWith("kpi_status_mismatch", expect.objectContaining({
      metric: "PSY", backend_status: "critical", frontend_tier: "normal",
    }));
  });

  it("여러 건이면 각각 보고", () => {
    reportStatusMismatches(
      { PSY: be("warning"), FARROWING_RATE: be("critical") },
      { PSY: "normal", FARROWING_RATE: "normal" },
    );
    expect(track).toHaveBeenCalledTimes(2);
  });
});

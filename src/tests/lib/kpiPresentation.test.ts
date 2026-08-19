import { describe, it, expect, vi, beforeEach } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { resolveKpiCards, reportPresentationGaps } from "@/lib/kpi/presentation";
import { KPI_CARD_REGISTRY } from "@/lib/kpi/cardRegistry";
import type { KpiPresentation, KpiDashboard } from "@/types/api.types";

vi.mock("@/lib/analytics", () => ({ track: vi.fn() }));
import { track } from "@/lib/analytics";

const item = (kpi_code: string, display_order: number | null, local_label: string | null = null) =>
  ({ kpi_code, display_order, local_label, priority_class: null, display_role: "PRIMARY" });

// 서버가 정렬을 끝낸 응답 — 프론트는 이 순서를 그대로 쓴다.
const BR: KpiPresentation = {
  country: "BR",
  headline_kpi: "PSY",
  items: [
    item("PSY", 10, "Desmamados por fêmea/ano"),
    item("FARROWING_RATE", 20, "Taxa de parição"),
    item("NPD", 30, "Dias não produtivos"),
  ],
};
const KR: KpiPresentation = {
  country: "KR",
  headline_kpi: "NPD",
  items: [item("NPD", 10, "비생산일수"), item("PSY", 20, null)],
};

const dash = (over: Partial<KpiDashboard> = {}) =>
  ({
    psy: 24.5, npd: 41.2, farrowing_rate: 87.3, sow_turnover: 2.31,
    benchmarks: {}, kpi_status: {}, alerts: [],
    ...over,
  } as unknown as KpiDashboard);

describe("G-A1 country divergence — 같은 build, 응답만 다르면 순서·명칭이 달라진다", () => {
  it("BR 응답 → BR 순서·명칭", () => {
    const r = resolveKpiCards(BR);
    expect(r.cards.map((c) => c.meta.kpi_code)).toEqual(["PSY", "FARROWING_RATE", "NPD"]);
    expect(r.cards[0].localLabel).toBe("Desmamados por fêmea/ano");
    expect(r.headlineKpi).toBe("PSY");
    expect(r.source).toBe("presentation");
  });

  it("KR 응답 → KR 순서·명칭 (코드 변경 0)", () => {
    const r = resolveKpiCards(KR);
    expect(r.cards.map((c) => c.meta.kpi_code)).toEqual(["NPD", "PSY"]);
    expect(r.cards[0].localLabel).toBe("비생산일수");
    expect(r.cards[1].localLabel).toBeNull();       // null이면 공용 라벨 사용
    expect(r.headlineKpi).toBe("NPD");
  });

  it("headline 은 서버 필드 — 프론트가 NORTH_STAR 를 탐색하지 않는다", () => {
    // priority_class 가 전부 null 이어도 headline_kpi 만으로 결정된다
    const r = resolveKpiCards({ ...BR, headline_kpi: "NPD" });
    expect(r.cards.find((c) => c.meta.kpi_code === "NPD")?.isHeadline).toBe(true);
    expect(r.cards.find((c) => c.meta.kpi_code === "PSY")?.isHeadline).toBe(false);
  });

  it("프론트가 재정렬하지 않는다 — display_order 가 뒤죽박죽이어도 응답 순서 유지", () => {
    const scrambled: KpiPresentation = {
      country: "BR", headline_kpi: null,
      items: [item("NPD", 99), item("PSY", 1), item("FARROWING_RATE", 50)],
    };
    expect(resolveKpiCards(scrambled).cards.map((c) => c.meta.kpi_code))
      .toEqual(["NPD", "PSY", "FARROWING_RATE"]);
  });

  it("★ presentation 계층 소스에 국가 코드 분기가 없다", () => {
    const root = resolve(__dirname, "../..");
    for (const f of ["lib/kpi/presentation.ts", "lib/kpi/cardRegistry.ts"]) {
      const src = readFileSync(resolve(root, f), "utf8");
      // 주석의 예시 문자열까지 걸리지 않도록 코드상의 비교/키 사용만 검사
      expect(src).not.toMatch(/country\s*===/);
      expect(src).not.toMatch(/["'](BR|KR|US|CN|VN|TH|MX)["']\s*[:)\]]/);
    }
  });
});

describe("G-A2 value invariance — presentation 은 숫자에 손대지 않는다", () => {
  it("정책이 바뀌어도 KPI 값 접근자 결과는 동일", () => {
    const d = dash();
    const before = resolveKpiCards(BR).cards.map((c) => c.meta.value(d));
    const after = resolveKpiCards(KR).cards
      .map((c) => c.meta.value(d));
    // 순서만 다를 뿐 값 자체는 같은 함수 결과
    expect(new Set(before)).toEqual(new Set([24.5, 87.3, 41.2]));
    expect(new Set(after)).toEqual(new Set([41.2, 24.5]));
    expect(resolveKpiCards(undefined).cards.find((c) => c.meta.kpi_code === "PSY")!.meta.value(d))
      .toBe(24.5);
  });

  it("값 없으면 null 그대로 — 다른 숫자로 대체하지 않는다", () => {
    const empty = dash({ psy: null, npd: null, farrowing_rate: null, sow_turnover: null });
    for (const c of resolveKpiCards(BR).cards) expect(c.meta.value(empty)).toBeNull();
  });

  it("레지스트리 접근자는 원값을 스케일 변환하지 않는다", () => {
    const d = dash({ npd: 41.2 });
    const npd = KPI_CARD_REGISTRY.find((m) => m.kpi_code === "NPD")!;
    expect(npd.value(d)).toBe(41.2);   // /1.6 같은 재계산 없음
  });
});

describe("G-A3 severity invariance — presentation 은 status 를 만들지 않는다", () => {
  it("resolveKpiCards 결과에 status/tier 필드가 없다", () => {
    for (const c of resolveKpiCards(BR).cards) {
      expect(c).not.toHaveProperty("status");
      expect(c).not.toHaveProperty("tier");
      expect(c).not.toHaveProperty("severity");
      expect(Object.keys(c).sort()).toEqual(["isHeadline", "localLabel", "meta"]);
    }
  });

  it("정책이 달라져도 동일 KPI 의 메타(=판정 입력)는 동일 객체", () => {
    const br = resolveKpiCards(BR).cards.find((c) => c.meta.kpi_code === "NPD")!;
    const kr = resolveKpiCards(KR).cards.find((c) => c.meta.kpi_code === "NPD")!;
    expect(br.meta).toBe(kr.meta);   // 레지스트리 단일 인스턴스 — 판정 입력 불변
  });
});

describe("G-A4 missing policy fail-safe", () => {
  beforeEach(() => vi.mocked(track).mockClear());

  it("미로드(undefined) → 기본 카드 순서 유지, 국가 추정 0", () => {
    const r = resolveKpiCards(undefined);
    expect(r.source).toBe("fallback");
    expect(r.headlineKpi).toBeNull();
    expect(r.cards.map((c) => c.meta.kpi_code)).toEqual(KPI_CARD_REGISTRY.map((m) => m.kpi_code));
    expect(r.cards.every((c) => c.localLabel === null)).toBe(true);
  });

  it("404/timeout(null) · items 빈 배열 → 동일 폴백", () => {
    for (const p of [null, { country: "BR", headline_kpi: null, items: [] } as KpiPresentation]) {
      expect(resolveKpiCards(p).source).toBe("fallback");
    }
  });

  it("items 가 배열이 아님(깨진 응답) → 크래시 없이 폴백", () => {
    const broken = { country: "BR", headline_kpi: null, items: undefined } as unknown as KpiPresentation;
    expect(() => resolveKpiCards(broken)).not.toThrow();
    expect(resolveKpiCards(broken).source).toBe("fallback");
  });

  it("★ Presentation 에는 있는데 Registry 에 없는 KPI → 건너뛰고 관측", () => {
    const p: KpiPresentation = {
      country: "BR", headline_kpi: "PSY",
      items: [item("PSY", 10), item("FCR_FUTURE", 20), item("NPD", 30)],
    };
    const r = resolveKpiCards(p);
    expect(r.cards.map((c) => c.meta.kpi_code)).toEqual(["PSY", "NPD"]);
    expect(r.unknownCodes).toEqual(["FCR_FUTURE"]);
    reportPresentationGaps(r);
    expect(track).toHaveBeenCalledWith("kpi_presentation_unknown_code",
      expect.objectContaining({ kpi_code: "FCR_FUTURE" }));
  });

  it("★ Registry 에는 있는데 Presentation 에 없는 KPI → 서버가 뺀 것이므로 미표시", () => {
    const r = resolveKpiCards({ country: "BR", headline_kpi: null, items: [item("PSY", 10)] });
    expect(r.cards.map((c) => c.meta.kpi_code)).toEqual(["PSY"]);
    expect(r.source).toBe("presentation");
  });

  it("★ 렌더 가능한 항목이 하나도 없으면 빈 화면 대신 기본 화면", () => {
    const r = resolveKpiCards({
      country: "BR", headline_kpi: null,
      items: [item("UNKNOWN_A", 10), item("UNKNOWN_B", 20)],
    });
    expect(r.source).toBe("fallback");
    expect(r.cards.length).toBe(KPI_CARD_REGISTRY.length);
    expect(r.unknownCodes).toEqual(["UNKNOWN_A", "UNKNOWN_B"]);
  });

  it("display_order 가 NULL 이어도 서버 순서를 그대로 쓴다(프론트 정렬 없음)", () => {
    const r = resolveKpiCards({
      country: "BR", headline_kpi: null,
      items: [item("NPD", null), item("PSY", null), item("FARROWING_RATE", 10)],
    });
    expect(r.cards.map((c) => c.meta.kpi_code)).toEqual(["NPD", "PSY", "FARROWING_RATE"]);
  });

  it("화면별 렌더 가능 코드 제한 — 목록 밖 KPI 는 제외되지만 크래시 없음", () => {
    const r = resolveKpiCards(BR, ["PSY", "NPD"]);
    expect(r.cards.map((c) => c.meta.kpi_code)).toEqual(["PSY", "NPD"]);
  });

  it("폴백 시 관측 이벤트 발생", () => {
    reportPresentationGaps(resolveKpiCards(undefined));
    expect(track).toHaveBeenCalledWith("kpi_presentation_fallback",
      expect.objectContaining({ reason: "absent_or_empty" }));
  });
});

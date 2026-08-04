import { describe, it, expect } from "vitest";
import {
  farrowingSchema,
  weaningSchema,
  matingSchema,
  pigletEventSchema,
  sowEntrySchema,
  finisherEntrySchema,
  firstError,
} from "@/lib/validation/eventSchemas";

// 클라이언트 사전검증 스키마 — 백엔드 validator와 동일 기준.
// tv=(k)=>k 통과기로 firstError가 i18n 코드를 그대로 반환하게 해 코드 단위 검증.
const tv = (k: string) => k;
const PAST = "2020-01-01";
const FUTURE = "2999-01-01";

describe("farrowingSchema (규칙별 격리)", () => {
  it("정상 → null", () => {
    expect(
      firstError(farrowingSchema, { farrowing_date: PAST, total_born: 12, born_alive: 11, stillborn: 1, mummified: 0 }, tv),
    ).toBeNull();
  });
  it("total_born>35 → totalBornMax", () => {
    expect(
      firstError(farrowingSchema, { farrowing_date: PAST, total_born: 36, born_alive: 0, stillborn: 0, mummified: 0 }, tv),
    ).toBe("totalBornMax");
  });
  it("합 불일치 → bornAliveSum", () => {
    expect(
      firstError(farrowingSchema, { farrowing_date: PAST, total_born: 12, born_alive: 10, stillborn: 1, mummified: 0 }, tv),
    ).toBe("bornAliveSum");
  });
  it("stillborn>25 → stillbornMax", () => {
    expect(
      firstError(farrowingSchema, { farrowing_date: PAST, total_born: 0, born_alive: 0, stillborn: 26, mummified: 0 }, tv),
    ).toBe("stillbornMax");
  });
  it("출생체중>3.0 → birthWeightMax", () => {
    expect(
      firstError(farrowingSchema, { farrowing_date: PAST, total_born: 0, born_alive: 0, stillborn: 0, mummified: 0, avg_birth_weight_kg: 3.5 }, tv),
    ).toBe("birthWeightMax");
  });
  it("미래일 → futureDate", () => {
    expect(
      firstError(farrowingSchema, { farrowing_date: FUTURE, total_born: 0, born_alive: 0, stillborn: 0, mummified: 0 }, tv),
    ).toBe("futureDate");
  });
});

describe("weaningSchema", () => {
  it("정상 → null", () => {
    expect(firstError(weaningSchema, { weaning_date: PAST, weaned_count: 10 }, tv)).toBeNull();
  });
  it("음수 → weanCountMin", () => {
    expect(firstError(weaningSchema, { weaning_date: PAST, weaned_count: -1 }, tv)).toBe("weanCountMin");
  });
  it("이유체중 범위밖 → weanWeightRange", () => {
    expect(firstError(weaningSchema, { weaning_date: PAST, weaned_count: 10, avg_weaning_weight_kg: 1.0 }, tv)).toBe("weanWeightRange");
  });
});

describe("matingSchema", () => {
  it("미래일 → futureDate, 과거 → null", () => {
    expect(firstError(matingSchema, { mating_date: FUTURE }, tv)).toBe("futureDate");
    expect(firstError(matingSchema, { mating_date: PAST }, tv)).toBeNull();
  });
});

describe("pigletEventSchema", () => {
  it("FOSTER_IN인데 target 없음 → fosterTargetRequired", () => {
    expect(firstError(pigletEventSchema, { event_type: "FOSTER_IN", event_date: PAST, piglet_count: 2 }, tv)).toBe("fosterTargetRequired");
  });
  it("DEATH는 target 불필요 → null", () => {
    expect(firstError(pigletEventSchema, { event_type: "DEATH", event_date: PAST, piglet_count: 1 }, tv)).toBeNull();
  });
});

describe("sowEntrySchema / finisherEntrySchema", () => {
  it("빈 귀표 → earTagRequired", () => {
    expect(firstError(sowEntrySchema, { ear_tag: "", entry_date: PAST, entry_type: "GILT" }, tv)).toBe("earTagRequired");
  });
  it("입식두수 0 → headCountMin", () => {
    expect(firstError(finisherEntrySchema, { group_code: "B-01", start_date: PAST, head_count_in: 0 }, tv)).toBe("headCountMin");
  });
});

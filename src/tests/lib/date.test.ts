import { describe, it, expect } from "vitest";
import { localToday, localDateOffset } from "@/lib/date";

// 로컬 캘린더 날짜 유틸 — UTC toISOString의 KST 하루밀림 버그 방지가 목적.
// 절대값은 시계 의존이라 형식·상대 불변식만 고정.

const YMD = /^\d{4}-\d{2}-\d{2}$/;

describe("localToday", () => {
  it("YYYY-MM-DD 형식", () => {
    expect(localToday()).toMatch(YMD);
  });
});

describe("localDateOffset", () => {
  it("형식 유지", () => {
    expect(localDateOffset(0)).toMatch(YMD);
    expect(localDateOffset(7)).toMatch(YMD);
    expect(localDateOffset(-7)).toMatch(YMD);
  });
  it("offset(0) == localToday()", () => {
    expect(localDateOffset(0)).toBe(localToday());
  });
  it("상대 순서: 미래>오늘>과거", () => {
    const past = localDateOffset(-1);
    const today = localToday();
    const future = localDateOffset(1);
    expect(past < today).toBe(true);
    expect(today < future).toBe(true);
  });
  it("114일 후는 오늘보다 크다(임신기간 예정일 계산 근거)", () => {
    expect(localDateOffset(114) > localToday()).toBe(true);
  });
});

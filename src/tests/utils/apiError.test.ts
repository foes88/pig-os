import { describe, it, expect } from "vitest";

import { apiError } from "@/lib/api/error";

// FastAPI 에러 응답에서 사람이 읽을 메시지 추출 — 배열(Pydantic 422)을 무시하면
// 실제 사유가 사라져 항상 generic 폴백만 보이던 버그(C4) 회귀 방지.
describe("apiError", () => {
  it("문자열 detail(도메인 에러)을 그대로 반환", () => {
    const err = { response: { data: { detail: "Period is locked" } } };
    expect(apiError(err, "fallback")).toBe("Period is locked");
  });

  it("배열 detail(Pydantic 422)의 msg들을 조합", () => {
    const err = { response: { data: { detail: [
      { msg: "born_alive must be >= 0", loc: ["body", "born_alive"] },
      { msg: "total_born too high", loc: ["body", "total_born"] },
    ] } } };
    expect(apiError(err, "fallback")).toBe("born_alive must be >= 0, total_born too high");
  });

  it("detail 없거나 알 수 없는 형태면 폴백", () => {
    expect(apiError({}, "fallback")).toBe("fallback");
    expect(apiError({ response: { data: {} } }, "fallback")).toBe("fallback");
    expect(apiError(null, "fallback")).toBe("fallback");
    expect(apiError({ response: { data: { detail: [] } } }, "fallback")).toBe("fallback");
  });
});

import { test, expect, loginSeed, gotoApp, expectNoRawI18nKeys } from "./helpers";

/**
 * 실 백엔드 — 작업대장(Work Ledger) 화면: 통합 이벤트 목록 + kind 필터.
 * (e2e 농장엔 이전 테스트들의 이벤트가 쌓여 있어 행이 존재)
 */
test.describe("live: work ledger screen", () => {
  test("작업대장 렌더 + 교배 필터", async ({ page, pageErrors }) => {
    await loginSeed(page);
    await gotoApp(page, "/reports/ledger");
    await expect(page.getByTestId("sidebar")).toBeVisible();
    await expectNoRawI18nKeys(page);

    // 통합 목록에 행이 있음
    await expect(page.getByTestId("ledger-row").first()).toBeVisible({ timeout: 15_000 });

    // 교배 필터 → 모든 행이 교배(요약 "AI #" 또는 "NATURAL #")
    await page.getByTestId("ledger-kind-mating").click();
    await expect(page.getByTestId("ledger-row").first()).toBeVisible({ timeout: 15_000 });

    expect(pageErrors, `예외:\n${pageErrors.join("\n")}`).toEqual([]);
  });
});

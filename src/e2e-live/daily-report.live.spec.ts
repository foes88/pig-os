import { test, expect, loginSeed, gotoApp, expectNoRawI18nKeys } from "./helpers";

/**
 * 실 백엔드 — 일일 사육현황 리포트 화면: 돈군 스냅샷 + 당일 이벤트 카드.
 */
test.describe("live: daily report screen", () => {
  test("일일보고 렌더 + 날짜 변경", async ({ page, pageErrors }) => {
    await loginSeed(page);
    await gotoApp(page, "/reports/daily");
    await expect(page.getByTestId("sidebar")).toBeVisible();
    await expectNoRawI18nKeys(page);

    // 날짜 입력 + 돈군 현황 카드 노출(로딩 종료 후)
    await expect(page.getByTestId("daily-date")).toBeVisible();
    await expect(page.getByText("Herd", { exact: true })).toBeVisible({ timeout: 15_000 });

    // 날짜 변경해도 크래시 없이 렌더
    await page.getByTestId("daily-date").fill("2026-01-01");
    await expect(page.getByTestId("sidebar")).toBeVisible();
    await expectNoRawI18nKeys(page);

    expect(pageErrors, `예외:\n${pageErrors.join("\n")}`).toEqual([]);
  });
});

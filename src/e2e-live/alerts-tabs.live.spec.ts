import { test, expect, loginSeed, gotoApp, expectNoRawI18nKeys } from "./helpers";

/**
 * 실 백엔드 — 알림 통합 화면 2탭(관리대상 ↔ 시스템알림) 전환.
 */
test.describe("live: alerts unified tabs", () => {
  test("관리대상/시스템알림 탭 전환 + 실데이터 렌더", async ({ page, pageErrors }) => {
    await loginSeed(page);

    await gotoApp(page, "/alerts");
    await expect(page.getByTestId("alerts-tab-alerts")).toBeVisible();
    await expect(page.getByTestId("alerts-tab-notifications")).toBeVisible();
    await expectNoRawI18nKeys(page);

    // 시스템알림 탭으로 전환 → /notifications
    await page.getByTestId("alerts-tab-notifications").click();
    await expect(page).toHaveURL(/\/notifications$/, { timeout: 30_000 });
    await expectNoRawI18nKeys(page);

    // 다시 관리대상 탭 → /alerts
    await page.getByTestId("alerts-tab-alerts").click();
    await expect(page).toHaveURL(/\/alerts$/, { timeout: 30_000 });

    expect(pageErrors, `예외:\n${pageErrors.join("\n")}`).toEqual([]);
  });
});

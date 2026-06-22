import { test, expect, loginSeed, gotoApp, expectNoRawI18nKeys } from "./helpers";

/**
 * 실 백엔드 읽기 — 인증 후 주요 화면이 실데이터로 크래시/원시키 없이 렌더되는지.
 * (mock 아님 → 실제 API 응답으로 렌더)
 */
const ROUTES = ["/", "/sows", "/boars", "/piglets", "/finishers", "/kpi", "/reports", "/reports/reproduction", "/reports/comprehensive-daily", "/alerts", "/alerts/open_overdue_mating", "/notifications", "/tasks", "/settings"];

test.describe("live: read across app", () => {
  test.beforeEach(async ({ page }) => {
    await loginSeed(page);
  });

  for (const route of ROUTES) {
    test(`${route} 실데이터 렌더(크래시/원시키 0)`, async ({ page, pageErrors }) => {
      const resp = await gotoApp(page, route);
      expect(resp?.status() ?? 200, `${route} HTTP`).toBeLessThan(400);
      await expect(page.getByTestId("sidebar")).toBeVisible();
      await expectNoRawI18nKeys(page);
      expect(pageErrors, `${route} 예외:\n${pageErrors.join("\n")}`).toEqual([]);
    });
  }
});

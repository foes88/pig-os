import { test, expect, loginSeed, expectNoRawI18nKeys } from "./helpers";

/**
 * 실 백엔드 인증 + 대시보드 — 시드 계정으로 실제 로그인 → 실 KPI 대시보드 렌더.
 * (실 /auth/login + /kpi/dashboard + /alerts + /notifications 왕복 검증)
 */
test.describe("live: auth & dashboard", () => {
  test("시드 계정 실로그인 → 대시보드가 크래시/원시키 없이 렌더", async ({ page, pageErrors }) => {
    await loginSeed(page);
    await expect(page).toHaveURL(/\/$|\/$/, { timeout: 10_000 });

    // 실 KPI 대시보드(빈 농장이어도 크래시 없어야 — alerts/benchmarks 포함)
    await expect(page.getByTestId("sidebar")).toBeVisible();
    await expectNoRawI18nKeys(page);
    expect(pageErrors, `대시보드 미처리 예외:\n${pageErrors.join("\n")}`).toEqual([]);
  });

  test("세션 쿠키 + 토큰 저장(실 로그인 결과)", async ({ page }) => {
    await loginSeed(page);
    const cookies = await page.context().cookies();
    expect(cookies.find((c) => c.name === "pigos_session")).toBeTruthy();
    const auth = await page.evaluate(() => localStorage.getItem("pigos-auth"));
    expect(auth).toContain("accessToken");
    expect(auth).toContain("932208a6"); // 시드 farm_id 일부
  });
});

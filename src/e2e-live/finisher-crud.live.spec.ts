import { test, expect, loginSeed, gotoApp, uniqueTag } from "./helpers";

/**
 * 실 백엔드 CRUD — 비육 그룹을 UI로 등록 → 실 DB 왕복 → 목록 반영.
 */
test.describe("live: finisher group create round-trip", () => {
  test("비육 그룹 등록 → 목록에 반영(실 DB)", async ({ page, pageErrors }) => {
    await loginSeed(page);
    await gotoApp(page, "/finishers");
    await expect(page.getByTestId("sidebar")).toBeVisible();

    const code = uniqueTag("FG");

    await page.getByTestId("finishers-add-btn").click();
    await expect(page.getByTestId("add-finisher-code")).toBeVisible();
    await page.getByTestId("add-finisher-code").fill(code);
    // 입식두수(필수) — 모달 내 첫 번째 number 입력
    await page.locator('[type="number"]').first().fill("100");
    await page.getByTestId("add-finisher-submit").click();

    await expect(page.getByText(code, { exact: true })).toBeVisible({ timeout: 15_000 });
    expect(pageErrors, `예외:\n${pageErrors.join("\n")}`).toEqual([]);
  });
});

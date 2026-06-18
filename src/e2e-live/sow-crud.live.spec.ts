import { test, expect, loginSeed, gotoApp, uniqueTag } from "./helpers";

/**
 * 실 백엔드 CRUD — 모돈을 UI로 등록 → 실제 DB 왕복 → 목록에 반영되는지.
 * (create → POST /sows → 쿼리 무효화 → 재조회 → 화면 반영의 풀 라운드트립)
 */
test.describe("live: sow create round-trip", () => {
  test("모돈 등록 → 목록에 즉시 반영(실 DB)", async ({ page, pageErrors }) => {
    await loginSeed(page);
    await gotoApp(page, "/sows");
    await expect(page.getByTestId("sidebar")).toBeVisible();

    const tag = uniqueTag("SOW");

    await page.getByTestId("sows-add-btn").click();
    const earInput = page.getByTestId("add-sow-ear-tag");
    await expect(earInput).toBeVisible();
    await earInput.fill(tag);
    await page.getByTestId("add-sow-submit").click();

    // 등록 성공 → 모달 닫힘 + 목록 재조회 → 새 귀표가 표에 보임
    await expect(page.getByText(tag, { exact: true })).toBeVisible({ timeout: 15_000 });
    expect(pageErrors, `예외:\n${pageErrors.join("\n")}`).toEqual([]);
  });
});

import { test, expect, loginSeed, gotoApp, createSowViaUI, recordSelectSow } from "./helpers";

/**
 * 실 백엔드 — 도폐사(Removal) 종료 처리: 모돈 도태 → 종료전이 + 활성 목록에서 제외.
 */
test.describe("live: sow removal (cull)", () => {
  test("도태 처리 → 성공 배너 + 활성 모돈 목록에서 사라짐", async ({ page, pageErrors }) => {
    test.slow();
    await loginSeed(page);
    const tag = await createSowViaUI(page, "CULL");
    await recordSelectSow(page, tag);

    // 도태(기본 CULLED, 오늘)
    await page.getByTestId("event-tab-cull").click();
    await page.getByTestId("event-save").click();
    await expect(page.getByText(new RegExp(`${tag} .*processed`))).toBeVisible({ timeout: 15_000 });

    // 활성 모돈 목록(/sows)에서 제외(종료 soft-delete) — 검색으로 narrow 후 0건
    await gotoApp(page, "/sows");
    await page.getByPlaceholder("Search by ear tag...").fill(tag);
    await expect(page.getByText(tag, { exact: true })).toHaveCount(0, { timeout: 15_000 });

    expect(pageErrors, `예외:\n${pageErrors.join("\n")}`).toEqual([]);
  });
});

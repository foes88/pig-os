import { test, expect, loginSeed, createSowViaUI, recordSelectSow, setPanelDate, daysAgo } from "./helpers";

/**
 * 실 백엔드 — 포유자돈 폐사: 분만(born_alive=10) 후 포유 중 폐사 1두 기록.
 */
test.describe("live: piglet death", () => {
  test("분만 후 자돈 폐사 기록(실 DB)", async ({ page, pageErrors }) => {
    test.slow();
    await loginSeed(page);
    const tag = await createSowViaUI(page, "PD");
    await recordSelectSow(page, tag);

    // 교배(150일전) → 분만(35일전, 10) → 포유 컨텍스트 확보
    await page.getByTestId("event-tab-mating").click();
    await setPanelDate(page, daysAgo(150));
    await page.getByTestId("event-save").click();
    await expect(page.getByText(`${tag} mating saved`)).toBeVisible({ timeout: 15_000 });

    await page.getByTestId("event-tab-farrowing").click();
    await setPanelDate(page, daysAgo(35));
    await page.getByTestId("stepper-Total born").fill("10");
    await page.getByTestId("event-save").click();
    await expect(page.getByText(new RegExp(`${tag} farrowing saved`))).toBeVisible({ timeout: 15_000 });

    // 자돈 폐사 1두 (포유기간 내 날짜)
    await page.getByTestId("event-tab-piglet_death").click();
    await setPanelDate(page, daysAgo(20));
    await page.getByTestId("event-save").click();
    await expect(page.getByText(new RegExp(`${tag} .*piglet deaths saved`))).toBeVisible({ timeout: 15_000 });

    expect(pageErrors, `예외:\n${pageErrors.join("\n")}`).toEqual([]);
  });
});

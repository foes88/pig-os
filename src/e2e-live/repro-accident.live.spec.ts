import { test, expect, loginSeed, createSowViaUI, recordSelectSow, setPanelDate, daysAgo } from "./helpers";

/**
 * 실 백엔드 — 번식사고(RTS): 교배(→PREGNANT) → 재발교배(RETURN_TO_ESTRUS) → 상태 ACCIDENT.
 */
test.describe("live: reproductive accident (RTS)", () => {
  test("교배 → RTS → 상태 ACCIDENT(실 DB)", async ({ page, pageErrors }) => {
    test.slow();
    await loginSeed(page);
    const tag = await createSowViaUI(page, "RTS");
    await recordSelectSow(page, tag);

    // 교배 → PREGNANT (30일 전)
    await page.getByTestId("event-tab-mating").click();
    await setPanelDate(page, daysAgo(30));
    await page.getByTestId("event-save").click();
    await expect(page.getByText(`${tag} mating saved`)).toBeVisible({ timeout: 15_000 });

    // 번식사고(RETURN_TO_ESTRUS 기본) → ACCIDENT
    await page.getByTestId("event-tab-repro").click();
    await setPanelDate(page, daysAgo(5));
    await page.getByTestId("event-save").click();
    await expect(page.getByText(new RegExp(`${tag} .* saved`))).toBeVisible({ timeout: 15_000 });

    // 재조회 → 상태 ACCIDENT (sowStatus.ACCIDENT = "RTS/Accident")
    await recordSelectSow(page, tag);
    await expect(page.getByText("RTS/Accident").first()).toBeVisible({ timeout: 15_000 });

    expect(pageErrors, `예외:\n${pageErrors.join("\n")}`).toEqual([]);
  });
});

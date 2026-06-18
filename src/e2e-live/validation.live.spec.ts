import { test, expect, loginSeed, createSowViaUI, recordSelectSow, setPanelDate, daysAgo } from "./helpers";

/**
 * 실 백엔드 — 검증 오류(422)가 화면에 표시되는지.
 * 분만(born_alive=10) 후, 이유두수를 공식에 안 맞게(3) 입력 → 백엔드 422 → 패널 에러 노출.
 */
test.describe("live: validation error surfaced", () => {
  test("이유두수 공식 불일치 → 422 에러 화면 표시 + 저장 안 됨", async ({ page }) => {
    test.slow();
    await loginSeed(page);
    const tag = await createSowViaUI(page, "VAL");
    await recordSelectSow(page, tag);

    // 교배(150일전) → 분만(35일전, 10)
    await page.getByTestId("event-tab-mating").click();
    await setPanelDate(page, daysAgo(150));
    await page.getByTestId("event-save").click();
    await expect(page.getByText(`${tag} mating saved`)).toBeVisible({ timeout: 15_000 });

    await page.getByTestId("event-tab-farrowing").click();
    await setPanelDate(page, daysAgo(35));
    await page.getByTestId("stepper-Total born").fill("10");
    await page.getByTestId("event-save").click();
    await expect(page.getByText(new RegExp(`${tag} farrowing saved`))).toBeVisible({ timeout: 15_000 });

    // 이유두수 3 (born_alive 10과 불일치) → 422
    await page.getByTestId("event-tab-weaning").click();
    await setPanelDate(page, daysAgo(14));
    await page.getByTestId("stepper-Weaned count").fill("3");
    await page.getByTestId("event-save").click();

    // 에러 표시 + "weaning saved" 미노출
    await expect(page.locator(".text-danger").first()).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(new RegExp(`${tag} weaning saved`))).toHaveCount(0);
  });
});

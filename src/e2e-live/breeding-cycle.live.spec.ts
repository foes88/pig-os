import { test, expect, loginSeed, createSowViaUI, recordSelectSow, setPanelDate, daysAgo } from "./helpers";

/**
 * 실 백엔드 — 번식 사이클 풀스택: 교배→분만→이유 (상태전이 + 날짜검증 통과).
 * 날짜: 입식 200일전 / 교배 150일전 / 분만 35일전(임신115일) / 이유 14일전(포유21일).
 * 각 단계 저장 성공 배너가 곧 상태전이 증명(분만=PREGNANT, 이유=LACTATING 필요).
 */
test.describe("live: breeding cycle", () => {
  test("교배→분만→이유 전체 사이클(실 DB, 상태전이)", async ({ page, pageErrors }) => {
    test.slow();
    await loginSeed(page);
    const tag = await createSowViaUI(page, "BC");
    await recordSelectSow(page, tag);

    // 교배 (GILT/OPEN → PREGNANT), 150일 전
    await page.getByTestId("event-tab-mating").click();
    await setPanelDate(page, daysAgo(150));
    await page.getByTestId("event-save").click();
    await expect(page.getByText(`${tag} mating saved`)).toBeVisible({ timeout: 15_000 });

    // 분만 (PREGNANT → LACTATING), 35일 전, 총산 10
    await page.getByTestId("event-tab-farrowing").click();
    await setPanelDate(page, daysAgo(35));
    await page.getByTestId("stepper-Total born").fill("10");
    await page.getByTestId("event-save").click();
    await expect(page.getByText(new RegExp(`${tag} farrowing saved`))).toBeVisible({ timeout: 15_000 });

    // 이유 (LACTATING → OPEN), 14일 전, 이유두수 10
    await page.getByTestId("event-tab-weaning").click();
    await setPanelDate(page, daysAgo(14));
    await page.getByTestId("stepper-Weaned count").fill("10");
    await page.getByTestId("event-save").click();
    await expect(page.getByText(new RegExp(`${tag} weaning saved`))).toBeVisible({ timeout: 15_000 });

    expect(pageErrors, `예외:\n${pageErrors.join("\n")}`).toEqual([]);
  });
});

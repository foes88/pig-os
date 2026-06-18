import { test, expect, loginSeed, createSowViaUI, recordSelectSow, setPanelDate, daysAgo } from "./helpers";

/**
 * 실 백엔드 — 이벤트 삭제 시 모돈 상태 롤백.
 * 교배(→PREGNANT) → 재조회로 상태 확인 → 교배 삭제 → 재조회 시 OPEN으로 롤백.
 * (검색으로 목록을 해당 모돈으로 필터 → 상태 배지가 단일·권위 있는 백엔드 상태)
 */
test.describe("live: event delete → status rollback", () => {
  test("교배 → PREGNANT → 교배 삭제 → OPEN 롤백", async ({ page, pageErrors }) => {
    test.slow();
    await loginSeed(page);
    const tag = await createSowViaUI(page, "RB");
    await recordSelectSow(page, tag);

    // 교배 → PREGNANT
    await page.getByTestId("event-tab-mating").click();
    await setPanelDate(page, daysAgo(150));
    await page.getByTestId("event-save").click();
    await expect(page.getByText(`${tag} mating saved`)).toBeVisible({ timeout: 15_000 });

    // 재조회 → 상태 PREGNANT 확인(목록 검색필터로 단일 모돈)
    await recordSelectSow(page, tag);
    await expect(page.getByText("Pregnant").first()).toBeVisible({ timeout: 15_000 });

    // 교배 삭제
    await expect(page.getByTestId("event-delete-mating")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("event-delete-mating").click();
    await page.getByTestId("event-delete-confirm").click();
    await expect(page.getByTestId("event-delete-mating")).toHaveCount(0, { timeout: 15_000 });

    // 재조회 → OPEN으로 롤백(PREGNANT 사라짐)
    await recordSelectSow(page, tag);
    await expect(page.getByText("Open").first()).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText("Pregnant")).toHaveCount(0);

    expect(pageErrors, `예외:\n${pageErrors.join("\n")}`).toEqual([]);
  });
});

import { test, expect, loginSeed, createSowViaUI, recordSelectSow, setPanelDate, gotoApp, uniqueTag } from "../helpers";

/**
 * UAT 2단계 갭 보강 — P0-FE 클라이언트 사전검증이 브라우저에 즉시 노출되는지.
 * (기존 validation.live.spec.ts는 백엔드 422 경로. 여기선 제출 전 Zod 게이트 확인.)
 */
function inDays(n: number): string {
  // 로컬 캘린더 기준 n일 후(YYYY-MM-DD). UTC toISOString은 KST 경계에서 하루 밀려 '미래'가 '오늘'이 됨.
  const d = new Date();
  d.setDate(d.getDate() + n);
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

test.describe("live: P0 client-side validation (UAT gap)", () => {
  test("교배 미래일 → 제출 전 클라 검증 에러 + 저장 안 됨 (FE-3)", async ({ page }) => {
    test.slow();
    await loginSeed(page);
    const tag = await createSowViaUI(page, "FUT");
    await recordSelectSow(page, tag);

    await page.getByTestId("event-tab-mating").click();
    await setPanelDate(page, inDays(1)); // 내일 = 미래
    await page.getByTestId("event-save").click();

    await expect(page.locator(".text-danger").first()).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(`${tag} mating saved`)).toHaveCount(0);
  });

  test("비육 입식체중 범위초과(>50kg) → 클라 검증 에러 + 등록 안 됨 (FE-7)", async ({ page }) => {
    await loginSeed(page);
    await gotoApp(page, "/finishers");
    const code = uniqueTag("FGW");

    await page.getByTestId("finishers-add-btn").click();
    await expect(page.getByTestId("add-finisher-code")).toBeVisible();
    await page.getByTestId("add-finisher-code").fill(code);
    await page.locator('[type="number"]').first().fill("100"); // 입식두수
    await page.locator('input[step="0.1"]').first().fill("80"); // 입식체중 80kg (>50 범위초과)
    await page.getByTestId("add-finisher-submit").click();

    // 클라 검증 에러 표시 + 그룹 미생성
    await expect(page.locator(".text-red-500").first()).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(code, { exact: true })).toHaveCount(0);
  });
});

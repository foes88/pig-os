import {
  test, expect, seedAuth, mockBackend, gotoApp, MOCK_FARM_ID,
} from "./helpers";

/**
 * /record 숫자 입력(Stepper) — 실제 타이핑이 값에 반영되는지.
 * (이전 회귀: Stepper가 <span>이라 +/- 클릭만 되고 타이핑 불가했음.)
 */

const SOW = {
  id: "22222222-2222-2222-2222-222222222222",
  farm_id: MOCK_FARM_ID,
  ear_tag: "E2E-001",
  parity: 3,
  status: "PREGNANT",
  breed: "Yorkshire",
  rfid_tag: null,
  entry_type: "GILT",
  date_of_birth: "2024-01-01",
  entry_date: "2024-06-01",
  cull_date: null,
  created_at: "2024-06-01T00:00:00Z",
  updated_at: "2024-06-01T00:00:00Z",
};

test.describe("record stepper typing", () => {
  test.beforeEach(async ({ page }) => {
    await seedAuth(page);
    await mockBackend(page);
    // 모돈 목록/검색이 최소 1마리 반환하도록 오버라이드 (route는 나중 등록이 우선)
    await page.route((u) => u.pathname.endsWith("/sows"), (route) => {
      if (route.request().method() !== "GET") {
        return route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
      }
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [SOW],
          meta: { total: 1, page: 1, page_size: 20, total_pages: 1 },
        }),
      });
    });
  });

  test("@smoke Stepper 입력란에 숫자를 직접 타이핑하면 값이 반영된다", async ({ page, pageErrors }) => {
    await gotoApp(page, "/record");
    // /record 첫 컴파일이 끝나 페이지 콘텐츠(검색창)까지 떠야 모돈 목록이 채워진다
    await expect(page).toHaveURL(/\/record$/, { timeout: 60_000 });
    await expect(page.getByTestId("sidebar")).toBeVisible();

    // 모돈 목록 행이 뜰 때까지 대기 후 선택 → farrowing 패널 + Stepper 노출
    const sowRow = page.getByText("E2E-001").first();
    await expect(sowRow).toBeVisible({ timeout: 60_000 });
    await sowRow.click();

    const stepper = page.locator('[data-testid^="stepper-"]').first();
    await expect(stepper).toBeVisible();

    // 타이핑으로 값 입력
    await stepper.fill("12");
    await expect(stepper).toHaveValue("12");

    // max(35) 초과 입력은 클램프
    await stepper.fill("99");
    await expect(stepper).toHaveValue("35");

    expect(pageErrors).toEqual([]);
  });
});

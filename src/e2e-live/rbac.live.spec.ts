import { test, expect, loginAs, gotoApp } from "./helpers";

/**
 * 실 백엔드 — 역할별 권한(RBAC).
 * 전제: scripts/seed_e2e_roles.py 로 viewer@/worker@ 시드됨.
 * OWNER=쓰기버튼 보임 / VIEWER=쓰기버튼 숨김 + 백엔드도 403.
 */
const PW = "e2e!2026pw";

test.describe("live: RBAC role gating", () => {
  test("OWNER는 모돈 등록 버튼이 보인다", async ({ page }) => {
    await loginAs(page, "e2e@pigos.io", PW);
    await gotoApp(page, "/sows");
    await expect(page.getByTestId("sows-add-btn")).toBeVisible({ timeout: 15_000 });
  });

  test("VIEWER는 모돈 등록 버튼이 숨겨진다(읽기전용)", async ({ page }) => {
    await loginAs(page, "viewer@pigos.io", PW);
    await gotoApp(page, "/sows");
    // 목록은 보이되(sidebar 떴고) 등록 버튼은 없음
    await expect(page.getByTestId("sidebar")).toBeVisible();
    await expect(page.getByTestId("sows-add-btn")).toHaveCount(0);
    // 비육 등록도 숨김
    await gotoApp(page, "/finishers");
    await expect(page.getByTestId("finishers-add-btn")).toHaveCount(0);
  });

  test("VIEWER는 기록입력(record)이 읽기전용 안내로 막힌다", async ({ page }) => {
    await loginAs(page, "viewer@pigos.io", PW);
    await gotoApp(page, "/record");
    await expect(page.getByTestId("sidebar")).toBeVisible();
    // 이벤트 저장 버튼이 아예 없음(읽기전용 게이트)
    await expect(page.getByTestId("event-save")).toHaveCount(0);
  });
});

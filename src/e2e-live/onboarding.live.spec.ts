import { test, expect, uniqueTag } from "./helpers";

/**
 * 자가 온보딩 — 로그인 없이 신규 고객이 조직+농장+계정을 만들고 바로 앱 진입하는 풀 라운드트립.
 * (출시 직결: 해외 고객 자가가입. 백엔드 POST /onboarding/complete → 토큰 발급 → 대시보드.)
 */
test.describe("live: self-onboarding", () => {
  test("신규 가입 → 조직·농장·계정 생성 → 대시보드 진입", async ({ page }) => {
    test.slow();
    const tag = uniqueTag("ONB").toLowerCase();
    const email = `${tag}@example.com`;

    await page.goto("http://localhost:3000/onboarding");

    // Step 0 — 조직/농장 (국가 기본 KR)
    await page.getByTestId("onb-org-name").fill(`Org ${tag}`);
    await page.getByTestId("onb-farm-name").fill(`Farm ${tag}`);
    await page.getByTestId("onb-next").click();

    // Step 1 — 사용자
    await page.getByTestId("onb-name").fill(`Owner ${tag}`);
    await page.getByTestId("onb-email").fill(email);
    await page.getByTestId("onb-password").fill("Onb12345!");
    await page.getByTestId("onb-confirm").fill("Onb12345!");
    await page.getByTestId("onb-next").click();

    // Step 2 — 검토 → 생성 제출
    await page.getByTestId("onb-next").click();

    // 생성 성공 → 앱 진입(사이드바 노출 = 로그인 상태)
    await expect(page.getByTestId("sidebar")).toBeVisible({ timeout: 20_000 });
  });
});

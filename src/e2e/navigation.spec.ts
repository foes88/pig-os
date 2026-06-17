import {
  test, expect, seedAuth, mockBackend, expectNoRawI18nKeys, gotoApp, clickNav,
} from "./helpers";

/**
 * 인증 후 주요 라우트 — 404/빈화면/크래시/원시 i18n 키 없이 렌더되는지.
 * 헤르메틱: 백엔드 호출은 mockBackend로 가로챔. 콘솔은 API 노이즈가 있을 수 있어
 * pageerror(미처리 예외)만 엄격히 검사한다.
 */

const ROUTES = ["/", "/sows", "/boars", "/piglets", "/finishers", "/record", "/kpi", "/reports", "/alerts", "/notifications", "/settings"];

test.describe("authenticated navigation", () => {
  test.beforeEach(async ({ page }) => {
    await seedAuth(page);
    await mockBackend(page);
  });

  for (const route of ROUTES) {
    test(`${route} 가 크래시/원시키 없이 렌더된다`, async ({ page, pageErrors }) => {
      const resp = await gotoApp(page, route);
      expect(resp?.status() ?? 200, `${route} HTTP 상태`).toBeLessThan(400);

      // chrome(사이드바)이 떠야 정상 앱 셸
      await expect(page.getByTestId("sidebar")).toBeVisible();
      await expectNoRawI18nKeys(page);
      expect(pageErrors, `${route} 미처리 예외:\n${pageErrors.join("\n")}`).toEqual([]);
    });
  }

  test("@smoke 사이드바 메뉴 클릭으로 라우팅된다", async ({ page, pageErrors }) => {
    await gotoApp(page, "/");
    await expect(page.getByTestId("sidebar")).toBeVisible();

    // 각 홉을 (컴파일된) 대시보드에서 시작 → 단일 클릭 라우팅 검증(체이닝 시 느린 2번째
    // 네비가 detach/취소되는 문제 회피). clickNav가 detach 재시도 + 긴 URL 대기를 흡수.
    await clickNav(page, "nav-sows", /\/sows$/);
    await gotoApp(page, "/");
    await clickNav(page, "nav-record", /\/record$/);
    await gotoApp(page, "/");
    await clickNav(page, "nav-alerts", /\/alerts$/);

    expect(pageErrors).toEqual([]);
  });

  test("@smoke ko 쿠키 → 메뉴와 내용이 한국어로 일치 표시", async ({ page }) => {
    await page.context().addCookies([
      { name: "NEXT_LOCALE", value: "ko", url: "http://localhost:3000" },
    ]);
    await gotoApp(page, "/");

    // 메뉴(chrome)가 한국어
    await expect(page.getByTestId("nav-dashboard")).toContainText("대시보드");
    // 원시 키 노출 없음 (내용 영역도 번역됨)
    await expectNoRawI18nKeys(page);
  });
});

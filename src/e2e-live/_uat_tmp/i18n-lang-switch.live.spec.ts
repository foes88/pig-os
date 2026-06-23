import { test, expect, loginAs, gotoApp, expectNoRawI18nKeys } from "../helpers";

/**
 * UAT §1 갭 보강 (2단계) — 5개 언어 전환 시 raw i18n 키 노출 0.
 * 기존 read.live는 en 로케일만 검사 → ko/zh/es/vi 미커버였던 갭을 채운다.
 *
 * 한국어(ko)는 플랫폼 관리자 전용(2026-06-22) → admin 계정으로 로그인해야 5개어가 모두 열림.
 * (FARM_OWNER로는 ko가 en으로 클램프됨.) admin 로그인 경로 + 5개어 번역 완전성을 함께 검증.
 *
 * 로케일 전환은 앱이 NEXT_LOCALE 쿠키 + router.refresh()로 처리(비동기).
 * 쿠키를 결정적으로 세팅 후 reload해 "각 로케일에서 raw i18n 키 0 + 스위처 반영"을 검증한다.
 */
const ADMIN_EMAIL = "admin@pigos.io";
const ADMIN_PASSWORD = "admin!2026pw";
const LOCALES = ["en", "ko", "zh", "es", "vi", "th", "pt"] as const;
const BASE = "http://localhost:3000";
const SHOTS = "e2e-live/_uat_tmp/shots";

test.describe("live: i18n 5-language (UAT §1 gap)", () => {
  test("5개 언어(en/ko/zh/es/vi) — 대시보드·/sows raw i18n 키 0 + 스위처 반영", async ({ page, context }) => {
    await loginAs(page, ADMIN_EMAIL, ADMIN_PASSWORD); // admin → ko 포함 5개어 노출

    for (const loc of LOCALES) {
      // 로케일을 쿠키로 결정적으로 지정(앱과 동일한 NEXT_LOCALE 메커니즘)
      await context.addCookies([{ name: "NEXT_LOCALE", value: loc, url: BASE }]);

      // 대시보드: 해당 로케일 렌더
      await gotoApp(page, "/");
      await expect(page.getByTestId("sidebar")).toBeVisible({ timeout: 20_000 });
      // 스위처가 쿠키 로케일을 반영(마운트 시 useEffect가 쿠키 읽음 → 재시도 내 수렴)
      await expect(page.getByTestId("language-switcher")).toHaveValue(loc, { timeout: 15_000 });
      // 핵심: raw i18n 키 노출 0
      await expectNoRawI18nKeys(page);
      await page.screenshot({ path: `${SHOTS}/dash_${loc}.png` });

      // 컨텐츠 페이지도 동일 로케일에서 raw 키 0
      await gotoApp(page, "/sows");
      await expect(page.getByTestId("sidebar")).toBeVisible({ timeout: 20_000 });
      await expectNoRawI18nKeys(page);
      await page.screenshot({ path: `${SHOTS}/sows_${loc}.png` });
    }
  });

  // 한국어 게이트(2026-06-22): 비관리자(FARM_OWNER)는 ko 선택 불가 + ko 쿠키는 en으로 클램프.
  test("비관리자(FARM_OWNER)는 한국어가 숨겨지고 ko 쿠키는 en으로 강제된다", async ({ page, context }) => {
    const { loginSeed } = await import("../helpers");
    await loginSeed(page); // e2e@pigos.io = FARM_OWNER
    // ko 쿠키를 강제로 심어도 en으로 클램프되어야 함
    await context.addCookies([{ name: "NEXT_LOCALE", value: "ko", url: BASE }]);
    await gotoApp(page, "/");
    await expect(page.getByTestId("sidebar")).toBeVisible({ timeout: 20_000 });
    // 스위처는 en으로 수렴(ko 클램프), ko 옵션 자체가 없음
    await expect(page.getByTestId("language-switcher")).toHaveValue("en", { timeout: 15_000 });
    const koOptions = await page.getByTestId("language-switcher").locator("option[value='ko']").count();
    expect(koOptions).toBe(0);
  });
});

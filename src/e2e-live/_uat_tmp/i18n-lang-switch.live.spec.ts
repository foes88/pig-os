import { test, expect, loginSeed, gotoApp, expectNoRawI18nKeys } from "../helpers";

/**
 * UAT §1 갭 보강 (2단계) — 5개 언어 전환 시 raw i18n 키 노출 0.
 * 기존 read.live는 en 로케일만 검사 → ko/zh/es/vi 미커버였던 갭을 채운다.
 *
 * 로케일 전환은 앱이 NEXT_LOCALE 쿠키 + router.refresh()로 처리(비동기).
 * select 조작은 refresh와 레이스가 나므로, 쿠키를 결정적으로 세팅 후 reload해
 * "각 로케일에서 raw i18n 키 0 + 스위처가 해당 로케일 반영"을 검증한다.
 * helpers 재사용(수정 없음). 격리 폴더(_uat_tmp).
 */
const LOCALES = ["en", "ko", "zh", "es", "vi"] as const;
const BASE = "http://localhost:3000";
const SHOTS = "e2e-live/_uat_tmp/shots";

test.describe("live: i18n 5-language (UAT §1 gap)", () => {
  test("5개 언어(en/ko/zh/es/vi) — 대시보드·/sows raw i18n 키 0 + 스위처 반영", async ({ page, context }) => {
    await loginSeed(page);

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
});

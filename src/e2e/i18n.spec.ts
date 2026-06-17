import { test, expect, expectNoRawI18nKeys, gotoApp, reloadApp, selectLoginLang } from "./helpers";

/**
 * 다국어 회귀 — 언어 지속성 + 모바일 언어 스위처 접근성 + 공개 페이지 원시 키 없음.
 */

const SUPPORTED = ["en", "ko", "zh", "es", "vi"] as const;

test.describe("i18n", () => {
  test("@smoke 언어 선택이 새로고침 후에도 유지된다", async ({ page }) => {
    await gotoApp(page, "/login");
    await selectLoginLang(page, "zh");
    await expect(page.getByRole("heading", { name: "欢迎回来" })).toBeVisible();

    await reloadApp(page);
    await expect(page.getByRole("heading", { name: "欢迎回来" })).toBeVisible();
  });

  test("모바일 뷰포트에서 모든 지원 언어에 접근 가능", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await gotoApp(page, "/login");

    // 드롭다운을 한 번 연 뒤(하이드레이션 안전) 모든 지원 언어 옵션이 보이는지 확인
    await expect(async () => {
      await page.getByTestId("language-switcher").click();
      await expect(page.getByTestId("language-option-en")).toBeVisible({ timeout: 1500 });
    }).toPass({ timeout: 30_000 });

    for (const lang of SUPPORTED) {
      await expect(page.getByTestId(`language-option-${lang}`)).toBeVisible();
    }
  });

  test("온보딩 페이지에 원시 i18n 키가 노출되지 않는다", async ({ page, pageErrors }) => {
    await page.context().addCookies([
      { name: "NEXT_LOCALE", value: "ko", url: "http://localhost:3000" },
    ]);
    const resp = await gotoApp(page, "/onboarding");
    expect(resp?.status() ?? 200).toBeLessThan(400);
    await expectNoRawI18nKeys(page);
    expect(pageErrors).toEqual([]);
  });
});

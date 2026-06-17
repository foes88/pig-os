import { test, expect, expectNoConsoleErrors, gotoApp, reloadApp, selectLoginLang } from "./helpers";

/**
 * 로그인 페이지 — 렌더링 / 언어 전환 / 아이디 저장.
 * 공개 페이지(백엔드 불필요). 콘솔 가드 엄격.
 */

test.describe("login", () => {
  test("@smoke 로그인 페이지가 핵심 요소와 함께 렌더된다", async ({ page, consoleErrors, pageErrors }) => {
    await gotoApp(page, "/login");

    await expect(page.getByTestId("login-email")).toBeVisible();
    await expect(page.getByTestId("login-password")).toBeVisible();
    await expect(page.getByTestId("login-submit")).toBeVisible();
    await expect(page.getByTestId("remember-id")).toBeVisible();
    await expect(page.getByTestId("language-switcher")).toBeVisible();

    expectNoConsoleErrors(consoleErrors, pageErrors);
  });

  test("@smoke 언어 전환 시 문구가 실제로 바뀐다 (en→ko)", async ({ page }) => {
    await gotoApp(page, "/login");

    // 기본 표시 후 한국어로 전환
    await selectLoginLang(page, "ko");
    await expect(page.getByRole("heading", { name: "다시 오셨군요" })).toBeVisible();

    // 영어로 전환 → 영어 문구
    await selectLoginLang(page, "en");
    await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible();

    // NEXT_LOCALE 쿠키가 함께 설정되어 앱 페이지와 언어가 일치하는지
    await selectLoginLang(page, "ko");
    const cookies = await page.context().cookies();
    expect(cookies.find((c) => c.name === "NEXT_LOCALE")?.value).toBe("ko");
  });

  test("@smoke 아이디 저장 체크 → 재방문 시 이메일 프리필", async ({ page }) => {
    // 로그인 시도는 실패시켜(401) 세션 쿠키 없이 /login에 머무르게 한다.
    await page.route((u) => u.pathname.endsWith("/auth/login"), (route) =>
      route.fulfill({ status: 401, contentType: "application/json", body: "{}" }),
    );

    await gotoApp(page, "/login");
    await page.getByTestId("login-email").fill("farmer@pigos.io");
    await page.getByTestId("login-password").fill("whatever");
    await page.getByTestId("remember-id").check();
    // 저장 로직은 API 호출 전에 실행되므로 로그인 실패(401)와 무관하게 저장됨.
    await page.getByTestId("login-submit").click();
    await expect(page.getByTestId("login-email")).toHaveValue("farmer@pigos.io");

    // 재방문 → 이메일 프리필 + 체크박스 유지
    await gotoApp(page, "/login");
    await expect(page.getByTestId("login-email")).toHaveValue("farmer@pigos.io");
    await expect(page.getByTestId("remember-id")).toBeChecked();
  });

  test("아이디 저장 해제 → 저장된 이메일 삭제", async ({ page }) => {
    await page.route((u) => u.pathname.endsWith("/auth/login"), (route) =>
      route.fulfill({ status: 401, contentType: "application/json", body: "{}" }),
    );

    // 저장된 이메일을 1회 시드(addInitScript는 매 네비마다 재시드되어 부적합)
    await gotoApp(page, "/login");
    await page.evaluate(() => localStorage.setItem("pigos_saved_email", "old@pigos.io"));
    await reloadApp(page);
    await expect(page.getByTestId("login-email")).toHaveValue("old@pigos.io");

    // 저장 해제 후 제출 → onSubmit이 저장 이메일 제거(API 호출 전 동기 실행)
    await page.getByTestId("remember-id").uncheck();
    await page.getByTestId("login-password").fill("whatever");
    await page.getByTestId("login-submit").click();

    // 재방문 시 더 이상 프리필되지 않아야 함(= 제거됨)
    await gotoApp(page, "/login");
    await expect(page.getByTestId("login-email")).toHaveValue("");
  });
});

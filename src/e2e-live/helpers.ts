import { test as base, expect, type Page } from "@playwright/test";

/**
 * 라이브 E2E 공용 — 실제 백엔드 로그인 + 콘솔 가드 + 고유 식별자.
 * 시드 계정(scripts/seed_e2e.py): e2e@pigos.io / e2e!2026pw (FARM_OWNER, 격리 농장).
 */

export const SEED_EMAIL = "e2e@pigos.io";
export const SEED_PASSWORD = "e2e!2026pw";

const CONSOLE_ALLOW = [
  /favicon/i, /ResizeObserver loop/i, /Download the React DevTools/i,
  /\[Fast Refresh\]/i, /hydrat/i,
];

type Fixtures = { consoleErrors: string[]; pageErrors: string[] };

export const test = base.extend<Fixtures>({
  consoleErrors: async ({ page }, use) => {
    const errors: string[] = [];
    page.on("console", (m) => {
      if (m.type() !== "error") return;
      const t = m.text();
      if (!CONSOLE_ALLOW.some((re) => re.test(t))) errors.push(t);
    });
    await use(errors);
  },
  pageErrors: async ({ page }, use) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await use(errors);
  },
});

export { expect };

export function gotoApp(page: Page, path: string) {
  return page.goto(path, { waitUntil: "domcontentloaded" });
}

/** 실제 UI 로그인(시드 계정) → 대시보드(사이드바) 진입까지 대기. */
export async function loginSeed(page: Page): Promise<void> {
  await gotoApp(page, "/login");
  await page.getByTestId("login-email").fill(SEED_EMAIL);
  await page.getByTestId("login-password").fill(SEED_PASSWORD);
  await page.getByTestId("login-submit").click();
  // 로그인 성공 → "/"로 replace. 사이드바가 뜨면 인증+초기 로드 완료.
  await expect(page.getByTestId("sidebar")).toBeVisible({ timeout: 30_000 });
}

/** 충돌 없는 고유 귀표/코드. (테스트 파일에선 Date.now 사용 가능) */
let _seq = 0;
const _base = Date.now().toString().slice(-7);
export function uniqueTag(prefix = "E2E"): string {
  _seq += 1;
  return `${prefix}-${_base}-${_seq}`;
}

/** N일 전 날짜(YYYY-MM-DD). 번식 사이클 날짜 검증(임신 100~130/포유 10~60)을 통과시키기 위함. */
export function daysAgo(n: number): string {
  return new Date(Date.now() - n * 86_400_000).toISOString().slice(0, 10);
}

/** 활성 패널의 날짜 입력(첫 type=date)을 설정. */
export async function setPanelDate(page: Page, dateStr: string): Promise<void> {
  await page.locator('input[type="date"]').first().fill(dateStr);
}

/** /sows에서 새 모돈 UI 등록 → 목록 반영까지 대기. 반환=귀표.
 *  entry_date를 과거로 소급(기본 200일 전)해 이벤트 날짜가 입식일 이후가 되도록. */
export async function createSowViaUI(page: Page, prefix = "BC"): Promise<string> {
  const tag = uniqueTag(prefix);
  await gotoApp(page, "/sows");
  await page.getByTestId("sows-add-btn").click();
  await page.getByTestId("add-sow-ear-tag").fill(tag);
  // 모달 내 입식일(type=date)을 200일 전으로
  await page.locator('input[type="date"]').first().fill(daysAgo(200));
  await page.getByTestId("add-sow-submit").click();
  await expect(page.getByText(tag, { exact: true })).toBeVisible({ timeout: 15_000 });
  return tag;
}

/** /record에서 해당 귀표 모돈을 검색→선택(우측 이벤트 패널 활성). */
export async function recordSelectSow(page: Page, tag: string): Promise<void> {
  await gotoApp(page, "/record");
  await page.getByPlaceholder("Search tag...").fill(tag);
  await page.getByText(tag, { exact: true }).click();
}

const I18N_NAMESPACES = [
  "prrsReport", "nav", "dashboard", "sows", "events", "kpi", "chat", "auth", "errors",
  "upgrade", "common", "sowStatus", "alerts", "validation", "settings", "reports", "users",
  "boars", "finishers", "piglets", "farrowing", "notifications", "sowDetail", "record",
  "addons", "reproReport", "growFinish", "settingsFarm", "benchmarks", "profile", "billing",
  "deleteAccount", "announcements", "support", "legal", "util", "tasks", "eventHistory",
  "insights", "thresholds",
];

export async function expectNoRawI18nKeys(page: Page): Promise<void> {
  const body = await page.locator("body").innerText();
  const re = new RegExp(`\\b(${I18N_NAMESPACES.join("|")})\\.[a-zA-Z][a-zA-Z0-9_.]*`, "g");
  const hits = body.match(re) ?? [];
  expect(hits, `원시 i18n 키 노출: ${hits.slice(0, 8).join(", ")}`).toEqual([]);
}

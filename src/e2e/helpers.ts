import { test as base, expect, type Page } from "@playwright/test";

/**
 * 공용 헬퍼 + 콘솔 가드 fixture.
 *
 *  - `test` : @playwright/test의 test를 확장. 각 테스트에서 발생한 console.error /
 *             pageerror(미처리 예외)를 수집한다. 테스트 본문에서 expectNoConsoleErrors()를
 *             호출해 단언한다(공개 페이지는 엄격, 인증 페이지는 pageerror만).
 *  - seedAuth(page)   : middleware 통과용 쿠키 + zustand persist(localStorage) 시드.
 *  - mockBackend(page): 모든 백엔드(8000) 호출을 가로채 빈/기본 데이터로 응답(헤르메틱).
 *  - expectNoRawI18nKeys(page) : 화면에 next-intl 원시 키(`nav.sows` 등) 노출 시 실패.
 */

export const MOCK_FARM_ID = "11111111-1111-1111-1111-111111111111";
export const API_ORIGIN = "http://localhost:8000";

// 무시해도 되는 콘솔 노이즈 (브라우저/프레임워크 자체 경고). 과하게 넓히지 말 것.
const CONSOLE_ALLOW = [
  /favicon/i,
  /ResizeObserver loop/i,
  /Download the React DevTools/i,
  /\[Fast Refresh\]/i,
  /hydrat/i, // dev 모드 hydration 경고는 별도 검증 대상 — 회귀 게이트에서는 제외
];

type Fixtures = {
  consoleErrors: string[];
  pageErrors: string[];
};

export const test = base.extend<Fixtures>({
  consoleErrors: async ({ page }, use) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() !== "error") return;
      const text = msg.text();
      if (CONSOLE_ALLOW.some((re) => re.test(text))) return;
      errors.push(text);
    });
    await use(errors);
  },
  pageErrors: async ({ page }, use) => {
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(err.message));
    await use(errors);
  },
});

export { expect };

/**
 * 'load' 이벤트는 next dev의 HMR 웹소켓/스트리밍으로 지연·중단(ERR_ABORTED)될 수 있어
 * domcontentloaded 기준으로 이동한다(상호작용 테스트엔 충분).
 */
export async function gotoApp(page: Page, path: string) {
  // dev 서버가 컴파일 중 일시적으로 멎으면 goto가 타임아웃날 수 있어 짧게 재시도한다.
  let lastErr: unknown;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      return await page.goto(path, { waitUntil: "domcontentloaded", timeout: 45_000 });
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr;
}
export function reloadApp(page: Page) {
  return page.reload({ waitUntil: "domcontentloaded" });
}

/**
 * 로그인 페이지 언어 선택 — 하이드레이션 전 클릭(핸들러 미연결)으로 드롭다운이
 * 안 열리는 레이스를 toPass 재시도로 흡수한 뒤 옵션을 선택한다.
 */
export async function selectLoginLang(page: Page, lang: string): Promise<void> {
  await expect(async () => {
    await page.getByTestId("language-switcher").click();
    await expect(page.getByTestId(`language-option-${lang}`)).toBeVisible({ timeout: 1500 });
  }).toPass({ timeout: 30_000 });
  await page.getByTestId(`language-option-${lang}`).click();
}

/**
 * 사이드바 메뉴 클릭 → 라우팅. dev 모드 주의점 2가지를 함께 흡수:
 *  - 하이드레이션 재렌더로 <a>가 잠깐 detach → Playwright click이 자동 재시도(단일 클릭).
 *  - 첫 방문 라우트는 온디맨드 컴파일로 URL 커밋이 느림 → 재클릭하지 말고 길게 대기
 *    (재클릭하면 진행 중 네비를 취소시켜 영원히 안 끝남).
 */
export async function clickNav(page: Page, testId: string, urlRe: RegExp): Promise<void> {
  const link = page.getByTestId(testId);
  await link.waitFor({ state: "visible", timeout: 30_000 });
  await link.click({ timeout: 15_000 });
  await expect(page).toHaveURL(urlRe, { timeout: 60_000 });
}

/** middleware(pigos_session 쿠키) + zustand persist(localStorage) 인증 시드. */
export async function seedAuth(page: Page): Promise<void> {
  await page.context().addCookies([
    { name: "pigos_session", value: "1", url: "http://localhost:3000" },
  ]);
  // localStorage는 페이지 로드 전 주입해야 store가 hydrate 시 읽는다.
  await page.addInitScript(
    ([farmId]) => {
      const payload = {
        state: {
          user: {
            id: "00000000-0000-0000-0000-000000000001",
            email: "e2e@pigos.io",
            name: "E2E Farm",
            role: "OWNER",
            farm_ids: [farmId],
          },
          accessToken: "e2e-access-token",
          refreshToken: "e2e-refresh-token",
          activeFarmId: farmId,
        },
        version: 0,
      };
      localStorage.setItem("pigos-auth", JSON.stringify(payload));
    },
    [MOCK_FARM_ID],
  );
}

/**
 * 백엔드 호출 전부 가로채 안전한 기본값 반환 (API 서버 불필요).
 * NEXT_PUBLIC_API_URL이 환경마다 다르므로(localhost / LAN IP / 도메인) origin이 아니라
 * 경로(`/api/...`, `/health`)로 매칭한다.
 */
export const isApiRequest = (url: URL) =>
  url.pathname.startsWith("/api/") || url.pathname === "/health";

export async function mockBackend(page: Page): Promise<void> {
  await page.route(isApiRequest, async (route) => {
    const url = route.request().url();
    const method = route.request().method();

    // 비-GET(mutation)은 빈 성공으로 처리
    if (method !== "GET") {
      return route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
    }

    const body = resolveMockBody(url);
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  });
}

function resolveMockBody(url: string): unknown {
  const u = url.split("?")[0];

  if (u.includes("/alerts/overdue")) return { total: 0, counts: {}, items: [] };
  if (u.includes("/alerts/cull-candidates")) return [];
  // 배열을 기대하는 리스트 엔드포인트들 (컴포넌트가 .forEach/.map 사용 → []로 응답)
  if (/\/(matings|farrowings|weanings|piglet_events)$/.test(u)) return [];
  if (u.endsWith("/notifications")) return { items: [], unread_count: 0, total: 0 };
  if (u.includes("/kpi/dashboard")) {
    return {
      farm_id: MOCK_FARM_ID, as_of: "2026-06-17", psy: null, npd: null,
      farrowing_rate: null, active_sows: 0, gestating: 0, lactating: 0, weaned: 0,
      week_matings: 0, week_farrowings: 0, week_weanings: 0, country: "KR",
      benchmarks: {}, alerts: [],
    };
  }
  if (u.includes("/kpi/")) return [];
  if (u.includes("/config")) {
    return { farm_id: MOCK_FARM_ID, gestation_length: 114, lactation_length: 21, wsi_days: 7 };
  }
  if (u.includes("/auth/me")) {
    return { user_id: MOCK_FARM_ID, email: "e2e@pigos.io", name: "E2E", role: "OWNER", farm_ids: [MOCK_FARM_ID] };
  }

  // 컬렉션 류는 PagedResult, 그 외는 빈 객체
  if (/\/(sows|boars|piglets|finisher-groups|tasks|events|reports)/.test(u)) {
    return { items: [], meta: { total: 0, page: 1, page_size: 20, total_pages: 0 } };
  }
  return {};
}

/** next-intl 원시 키(`nav.sows`, `dashboard.title` 등) 화면 노출 감지 → 실패. */
const I18N_NAMESPACES = [
  "prrsReport", "nav", "dashboard", "sows", "events", "kpi", "chat", "auth", "errors",
  "upgrade", "common", "sowStatus", "alerts", "validation", "settings", "reports", "users",
  "boars", "finishers", "piglets", "farrowing", "notifications", "sowDetail", "record",
  "addons", "reproReport", "growFinish", "settingsFarm", "benchmarks", "profile", "billing",
  "deleteAccount", "announcements", "support", "legal", "util", "tasks", "eventHistory",
  "insights", "thresholds",
];

export async function expectNoRawI18nKeys(page: Page): Promise<void> {
  const bodyText = await page.locator("body").innerText();
  const re = new RegExp(`\\b(${I18N_NAMESPACES.join("|")})\\.[a-zA-Z][a-zA-Z0-9_.]*`, "g");
  const hits = bodyText.match(re) ?? [];
  expect(hits, `원시 i18n 키가 화면에 노출됨: ${hits.slice(0, 8).join(", ")}`).toEqual([]);
}

export function expectNoConsoleErrors(consoleErrors: string[], pageErrors: string[]): void {
  expect(pageErrors, `미처리 페이지 예외:\n${pageErrors.join("\n")}`).toEqual([]);
  expect(consoleErrors, `콘솔 에러:\n${consoleErrors.join("\n")}`).toEqual([]);
}

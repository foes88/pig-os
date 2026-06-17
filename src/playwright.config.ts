import { defineConfig, devices } from "@playwright/test";

/**
 * PigOS E2E — focused 회귀 방지 스위트 (Chromium 단일).
 *
 * 목표: pytest/tsc/vitest로는 구조적으로 못 잡는 "실제 브라우저 상호작용" 버그
 *   (언어 전환, 숫자 타이핑, 라우팅, 로그인 흐름, 원시 i18n 키 노출)를 커밋 전에 차단.
 *
 * 실행:
 *   npm run test:e2e        — 전체 E2E (headless)
 *   npm run test:e2e:smoke  — @smoke 태그만 (CI/커밋 전 빠른 게이트)
 *   npm run test:e2e:ui     — Playwright UI 모드 (디버깅)
 *
 * 헤르메틱 설계: 모든 백엔드(http://localhost:8000) 호출을 page.route로 가로채므로
 *   API 서버 없이도 동작한다. dev 서버(next)만 자동 기동/재사용.
 */
export default defineConfig({
  testDir: "./e2e",
  // 단일 dev 서버의 온디맨드 컴파일을 여러 워커가 동시에 두드리면 첫 방문이 매우 느려져
  // 타임아웃/하이드레이션 레이스를 유발 → focused 게이트는 직렬 실행으로 결정성 확보.
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  // dev 서버 첫 방문 온디맨드 컴파일은 가끔 액션 타임아웃을 넘김 → 1회 재시도(워밍 후 통과).
  // CI에서 production 빌드(next start)로 돌리면 온디맨드 컴파일이 없어 더 안정적.
  retries: process.env.CI ? 2 : 1,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : [["list"]],
  // next dev(turbopack)는 라우트 첫 방문 시 온디맨드 컴파일 → 첫 네비가 느릴 수 있어 넉넉히.
  timeout: 90_000,
  expect: { timeout: 10_000 },

  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    locale: "en-US",
    navigationTimeout: 60_000,
    actionTimeout: 15_000,
  },

  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],

  // dev 서버 자동 기동 (이미 떠 있으면 재사용 → 로컬 개발 흐름 방해 안 함)
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});

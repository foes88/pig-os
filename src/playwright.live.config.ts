import { defineConfig, devices } from "@playwright/test";

/**
 * PigOS 라이브 E2E — 실제 API+DB 상대 (NON-hermetic).
 *
 * `src/e2e/`(헤르메틱·mock)와 분리. 실제 백엔드가 떠 있어야 한다:
 *   docker compose up -d postgres redis
 *   cd api && uv run alembic upgrade head
 *   cd api && PYTHONPATH=. uv run python scripts/seed_e2e.py
 *   cd api && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
 *
 * 실행: npm run test:e2e:live  /  test:e2e:live:ui
 * 웹은 .env.local의 NEXT_PUBLIC_API_URL로 백엔드 호출 → 그 API가 살아있어야 통과.
 */
export default defineConfig({
  testDir: "./e2e-live",
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: 1,
  reporter: [["list"]],
  timeout: 90_000,
  expect: { timeout: 12_000 },

  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    locale: "en-US",
    navigationTimeout: 60_000,
    actionTimeout: 15_000,
  },

  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],

  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});

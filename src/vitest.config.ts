import { defineConfig, configDefaults } from "vitest/config";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

// Run: npm install -D vitest jsdom @vitejs/plugin-react @testing-library/react \
//        @testing-library/user-event @testing-library/jest-dom
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
    // E2E(Playwright) 스펙은 vitest가 잡지 않도록 제외 — 별도 러너로 실행
    exclude: [...configDefaults.exclude, "e2e/**"],
  },
  resolve: { alias: { "@": resolve(__dirname, ".") } },
});

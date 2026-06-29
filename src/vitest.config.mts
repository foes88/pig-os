import { defineConfig, configDefaults } from "vitest/config";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

// Run: npm install -D vitest jsdom @vitejs/plugin-react @testing-library/react \
//        @testing-library/user-event @testing-library/jest-dom
export default defineConfig({
  plugins: [react()],
  // tsconfig는 jsx:"preserve"(Next 기본) → vitest esbuild가 classic 런타임으로 폴백해
  // 테스트 .tsx에서 "React is not defined" 발생. 자동 런타임 명시로 해소.
  esbuild: { jsx: "automatic", jsxImportSource: "react" },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
    // E2E(Playwright) 스펙은 vitest가 잡지 않도록 제외 — 별도 러너로 실행
    exclude: [...configDefaults.exclude, "e2e/**", "e2e-live/**"],
  },
  resolve: { alias: { "@": resolve(__dirname, ".") } },
});

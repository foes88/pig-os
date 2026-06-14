import { defineConfig } from "vitest/config";
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
  },
  resolve: { alias: { "@": resolve(__dirname, ".") } },
});

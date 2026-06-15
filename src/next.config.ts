import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./i18n/request.ts");

const nextConfig: NextConfig = {
  // Docker prod: .next/standalone + `node server.js` 산출 (src/Dockerfile에서 사용)
  output: "standalone",
};

export default withNextIntl(nextConfig);

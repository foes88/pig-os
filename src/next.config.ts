import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./i18n/request.ts");

// 백엔드 프록시 타깃(서버사이드). 클라는 상대경로(/api/v1)로 호출 → Next 서버가 여기로 전달.
// 브라우저가 LAN IP(192.168.x)를 직접 잡지 않아도 되므로 PC/폰/VPN 무관하게 동작.
const API_PROXY_TARGET = process.env.API_PROXY_TARGET ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Docker prod: .next/standalone + `node server.js` 산출 (src/Dockerfile에서 사용)
  output: "standalone",
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${API_PROXY_TARGET}/api/:path*` },
      { source: "/health", destination: `${API_PROXY_TARGET}/health` },
    ];
  },
};

export default withNextIntl(nextConfig);

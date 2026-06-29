import "@testing-library/jest-dom";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => cleanup());

// ── 전역 공통 mock ──────────────────────────────────────────────────────────
// next/navigation·next-intl은 거의 모든 페이지/탭 컴포넌트가 사용 → 한 곳에서 완전한
// 형태로 mock해 개별 테스트의 부분 mock 누락(usePathname/useLocale 등)으로 인한
// 깨짐을 방지한다. 특정 반환값이 필요한 테스트는 파일 내 vi.mock으로 덮어쓸 수 있다.
vi.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({
    push: vi.fn(), replace: vi.fn(), refresh: vi.fn(), back: vi.fn(),
    forward: vi.fn(), prefetch: vi.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({}),
}));

vi.mock("next-intl", () => ({
  useTranslations: () => (k: string) => k,
  useLocale: () => "en",
}));

import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { Sidebar } from "@/components/Sidebar";
import { renderWithClient } from "../test-utils";

vi.mock("next/navigation", () => ({ usePathname: () => "/" }));
vi.mock("next/image", () => ({ default: () => null }));
vi.mock("@/store/auth.store", () => ({
  useAuthStore: (sel: (s: { user: unknown; activeFarmId: string | null }) => unknown) =>
    sel({ user: { name: "Test Farm" }, activeFarmId: null }),
}));

describe("Sidebar", () => {
  it("renders the primary nav items", () => {
    // 라벨은 messages 파일 단일소스(next-intl은 setup에서 key 반환 mock) →
    // 번역 텍스트 대신 안정적인 nav testid로 렌더 검증.
    renderWithClient(<Sidebar />);
    for (const id of ["nav-dashboard", "nav-sows", "nav-boars", "nav-settings", "nav-reports-sow-status"]) {
      expect(screen.getByTestId(id)).toBeTruthy();
    }
  });
});

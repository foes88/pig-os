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
  it("renders the primary nav labels", () => {
    renderWithClient(<Sidebar lang="ko" />);
    for (const label of ["대시보드", "모돈", "웅돈", "보고서", "설정"]) {
      expect(screen.getAllByText(label).length).toBeGreaterThan(0);
    }
  });
});

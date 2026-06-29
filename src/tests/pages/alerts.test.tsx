import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithClient } from "../test-utils";

// next-intl·next/navigation은 tests/setup.ts에서 전역 mock (완전한 형태).
vi.mock("next/link", () => ({ default: ({ children }: { children: React.ReactNode }) => <>{children}</> }));
vi.mock("@/store/auth.store", () => ({
  useAuthStore: (sel: (s: { activeFarmId: string | null }) => unknown) => sel({ activeFarmId: "farm-1" }),
}));
vi.mock("@/lib/api/endpoints/alerts", () => ({
  alertsApi: {
    overdue: vi.fn().mockResolvedValue({
      total: 1,
      counts: { open_overdue_mating: 1 },
      items: [{ type: "open_overdue_mating", sow_id: "s1", ear_tag: "A-001", status: "OPEN", parity: 2, overdue_days: 10 }],
    }),
    cullCandidates: vi.fn().mockResolvedValue([
      { sow_id: "s2", ear_tag: "B-007", status: "OPEN", parity: 9, reasons: ["aged_low_performer"], last_weaned: 7 },
    ]),
  },
}));

import AlertsPage from "@/app/(app)/alerts/page";

describe("AlertsPage", () => {
  it("renders the header", () => {
    renderWithClient(<AlertsPage />);
    expect(screen.getByText("title")).toBeInTheDocument();  // next-intl mock → 키 반환
  });

  it("shows an overdue sow row after data loads", async () => {
    renderWithClient(<AlertsPage />);
    // SignalCard는 "A-001 · Open"을 한 노드에 렌더 → 부분일치 matcher 사용.
    expect(await screen.findByText(/A-001/)).toBeInTheDocument();
  });

  it("shows a cull candidate after data loads", async () => {
    renderWithClient(<AlertsPage />);
    expect(await screen.findByText("B-007")).toBeInTheDocument();
  });
});

import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";

import { renderWithClient } from "../test-utils";

// next-intl·next/navigation은 tests/setup.ts에서 전역 mock (완전한 형태).
vi.mock("@/store/auth.store", () => ({
  useAuthStore: (sel: (s: { activeFarmId: string | null }) => unknown) => sel({ activeFarmId: "farm-1" }),
}));
vi.mock("@/lib/api/endpoints/kpi", () => ({
  kpiApi: { dashboard: vi.fn().mockResolvedValue({ alerts: [] }) },
}));
vi.mock("@/lib/api/endpoints/notifications", () => ({
  notificationsApi: {
    list: vi.fn().mockResolvedValue({ items: [], unread_count: 0, total: 0 }),
    markRead: vi.fn().mockResolvedValue({ updated: 1, unread_count: 0 }),
    markAllRead: vi.fn().mockResolvedValue({ updated: 0, unread_count: 0 }),
  },
}));

import NotificationsPage from "@/app/(app)/notifications/page";

describe("NotificationsPage", () => {
  it("renders the title and both sections", () => {
    renderWithClient(<NotificationsPage />);
    expect(screen.getByText("title")).toBeInTheDocument();
    expect(screen.getByText("realtimeSection")).toBeInTheDocument();
    expect(screen.getByText("savedSection")).toBeInTheDocument();
  });

  it("shows the saved empty state after data loads", async () => {
    renderWithClient(<NotificationsPage />);
    expect(await screen.findByText("savedEmpty")).toBeInTheDocument();
  });
});

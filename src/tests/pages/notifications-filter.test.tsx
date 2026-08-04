import { describe, it, expect, vi } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithClient } from "../test-utils";

// 알림 심각도 필터(CRITICAL/WARNING/INFO 탭) 동작. next-intl 전역 mock((k)=>k).
vi.mock("@/store/auth.store", () => ({
  useAuthStore: (sel: (s: { activeFarmId: string | null }) => unknown) => sel({ activeFarmId: "farm-1" }),
}));
vi.mock("@/lib/api/endpoints/kpi", () => ({
  kpiApi: {
    dashboard: vi.fn().mockResolvedValue({
      alerts: [
        { severity: "CRITICAL", rule_id: "r1", kpi: "PSY", message: "crit-msg" },
        { severity: "WARNING", rule_id: "r2", kpi: "NPD", message: "warn-msg" },
        { severity: "INFO", rule_id: "r3", kpi: "FCR", message: "info-msg" },
      ],
    }),
  },
}));
vi.mock("@/lib/api/endpoints/notifications", () => ({
  notificationsApi: {
    list: vi.fn().mockResolvedValue({ items: [], unread_count: 0, total: 0 }),
    markRead: vi.fn().mockResolvedValue({ updated: 1, unread_count: 0 }),
    markAllRead: vi.fn().mockResolvedValue({ updated: 0, unread_count: 0 }),
  },
}));

import NotificationsPage from "@/app/(app)/notifications/page";

function severityTab(label: string) {
  // 심각도 탭은 버튼(카드 배지는 span) → 버튼 중 라벨 포함하는 것
  return screen.getAllByRole("button").find((b) => b.textContent?.includes(label))!;
}

describe("NotificationsPage 심각도 필터", () => {
  it("ALL은 전체, 탭 선택 시 해당 심각도만 표시", async () => {
    renderWithClient(<NotificationsPage />);
    // 초기 ALL: 3건 모두
    expect(await screen.findByText("crit-msg")).toBeInTheDocument();
    expect(screen.getByText("warn-msg")).toBeInTheDocument();
    expect(screen.getByText("info-msg")).toBeInTheDocument();

    // CRITICAL 탭 → crit만
    fireEvent.click(severityTab("sevCritical"));
    expect(screen.getByText("crit-msg")).toBeInTheDocument();
    expect(screen.queryByText("warn-msg")).not.toBeInTheDocument();
    expect(screen.queryByText("info-msg")).not.toBeInTheDocument();

    // WARNING 탭 → warn만
    fireEvent.click(severityTab("sevWarning"));
    expect(screen.getByText("warn-msg")).toBeInTheDocument();
    expect(screen.queryByText("crit-msg")).not.toBeInTheDocument();
  });

  it("각 심각도 탭에 건수 노출(ALL=3, CRITICAL=1)", async () => {
    renderWithClient(<NotificationsPage />);
    await screen.findByText("crit-msg");
    expect(severityTab("filterAll").textContent).toContain("3");
    expect(severityTab("sevCritical").textContent).toContain("1");
  });
});

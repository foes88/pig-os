import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";

import { renderWithClient } from "../test-utils";

// next-intl·next/navigation은 setup.ts 전역 mock.
vi.mock("next/link", () => ({ default: ({ children }: { children: React.ReactNode }) => <>{children}</> }));
vi.mock("@/store/auth.store", () => ({
  useAuthStore: (sel: (s: { activeFarmId: string | null; user: { name: string } }) => unknown) =>
    sel({ activeFarmId: "farm-1", user: { name: "Tester" } }),
}));

const h = vi.hoisted(() => ({ dashboard: vi.fn(), overdue: vi.fn(), tasks: vi.fn() }));
vi.mock("@/lib/api/endpoints/kpi", () => ({ kpiApi: { dashboard: h.dashboard } }));
vi.mock("@/lib/api/endpoints/alerts", () => ({ alertsApi: { overdue: h.overdue } }));
vi.mock("@/lib/api/endpoints/tasks", () => ({ tasksApi: { list: h.tasks } }));

import Dashboard from "@/app/(app)/page";

describe("Dashboard 상태 처리", () => {
  it("KPI 로드 실패 시 에러를 보인다(빈 화면 아님)", async () => {
    h.dashboard.mockRejectedValueOnce(new Error("500"));
    h.overdue.mockResolvedValueOnce({ total: 0, counts: {}, items: [] });
    h.tasks.mockResolvedValueOnce([]);
    renderWithClient(<Dashboard />);
    expect(await screen.findByText("loadError")).toBeInTheDocument();
  });

  it("정상 데이터면 제목을 렌더한다", async () => {
    h.dashboard.mockResolvedValueOnce({
      as_of: "2026-06-29", active_sows: 100, psy: 24.5, npd: 35, farrowing_rate: 86, alerts: [],
    });
    h.overdue.mockResolvedValueOnce({ total: 0, counts: {}, items: [] });
    h.tasks.mockResolvedValueOnce([]);
    renderWithClient(<Dashboard />);
    expect(await screen.findByText("title")).toBeInTheDocument();
  });
});

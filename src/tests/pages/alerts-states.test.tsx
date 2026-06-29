import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";

import { renderWithClient } from "../test-utils";

// next-intl·next/navigation은 setup.ts 전역 mock.
vi.mock("next/link", () => ({ default: ({ children }: { children: React.ReactNode }) => <>{children}</> }));
vi.mock("@/store/auth.store", () => ({
  useAuthStore: (sel: (s: { activeFarmId: string | null }) => unknown) => sel({ activeFarmId: "farm-1" }),
}));

const h = vi.hoisted(() => ({
  overdue: vi.fn(),
  culls: vi.fn(),
}));
vi.mock("@/lib/api/endpoints/alerts", () => ({
  alertsApi: { overdue: h.overdue, cullCandidates: h.culls },
}));

import AlertsPage from "@/app/(app)/alerts/page";

describe("AlertsPage 상태 처리", () => {
  it("API 실패 시 에러를 보이고, 거짓 '이상 없음'을 보이지 않는다", async () => {
    h.overdue.mockRejectedValueOnce(new Error("network"));
    h.culls.mockResolvedValueOnce([]);
    renderWithClient(<AlertsPage />);
    expect(await screen.findByText("loadError")).toBeInTheDocument();
    expect(screen.queryByText(/emptyOverdueTitle/)).not.toBeInTheDocument();
  });

  it("데이터가 비어 있으면(정상 응답) '이상 없음' 빈 상태를 보인다", async () => {
    h.overdue.mockResolvedValueOnce({ total: 0, counts: {}, items: [] });
    h.culls.mockResolvedValueOnce([]);
    renderWithClient(<AlertsPage />);
    expect(await screen.findByText(/emptyOverdueTitle/)).toBeInTheDocument();
    expect(screen.queryByText("loadError")).not.toBeInTheDocument();
  });
});

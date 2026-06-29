import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";

import { renderWithClient } from "../test-utils";

// next-intl은 setup.ts 전역 mock. next/navigation은 useSearchParams를 딥링크용으로 덮어씀.
vi.mock("next/navigation", () => ({
  usePathname: () => "/record",
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), prefetch: vi.fn(), refresh: vi.fn(), back: vi.fn() }),
  useSearchParams: () => new URLSearchParams("tab=mating&sowId=s1"),
  useParams: () => ({}),
}));
vi.mock("@/store/auth.store", () => ({
  useAuthStore: (sel: (s: { activeFarmId: string | null; user: { role: string } }) => unknown) =>
    sel({ activeFarmId: "farm-1", user: { role: "FARM_OWNER" } }),
}));
vi.mock("@/lib/api/endpoints/sows", () => ({
  sowsApi: {
    list: vi.fn().mockResolvedValue({
      items: [{ id: "s1", ear_tag: "A-001", status: "OPEN", parity: 2, entry_date: "2024-01-01" }],
      total: 1,
    }),
    cull: vi.fn(),
  },
}));
vi.mock("@/lib/api/endpoints/events", () => ({
  eventsApi: {
    matings: { list: vi.fn().mockResolvedValue([]), create: vi.fn(), remove: vi.fn(), update: vi.fn() },
    farrowings: { list: vi.fn().mockResolvedValue([]), create: vi.fn(), remove: vi.fn(), update: vi.fn() },
    weanings: { list: vi.fn().mockResolvedValue([]), create: vi.fn(), remove: vi.fn(), update: vi.fn() },
    pregnancyChecks: { create: vi.fn() },
    reproductive: { create: vi.fn() },
    pigletEvents: { create: vi.fn() },
  },
}));

import RecordPage from "@/app/(app)/record/page";

describe("RecordPage 딥링크 (C2)", () => {
  it("?sowId=로 들어오면 해당 모돈을 자동 선택한다", async () => {
    renderWithClient(<RecordPage />);
    // 선택된 모돈 헤더에 ear_tag가 나타나면 자동선택 성공(딥링크 전 빈 폼이던 버그 해소).
    expect(await screen.findAllByText(/A-001/)).not.toHaveLength(0);
  });
});

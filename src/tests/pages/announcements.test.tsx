import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithClient } from "../test-utils";

// next-intl 전역 mock. contentApi만 개별 mock(useQuery로 로드).
const h = vi.hoisted(() => ({
  items: [] as Array<Record<string, unknown>>,
}));
vi.mock("@/lib/api/endpoints/content", () => ({
  contentApi: { announcements: vi.fn(() => Promise.resolve(h.items)) },
}));

import AnnouncementsPage from "@/app/(app)/announcements/page";

describe("AnnouncementsPage", () => {
  beforeEach(() => {
    h.items = [];
  });

  it("공지 없으면 빈 상태 노출", async () => {
    renderWithClient(<AnnouncementsPage />);
    expect(await screen.findByText("empty")).toBeInTheDocument();
  });

  it("공지 있으면 제목·본문·분류 렌더", async () => {
    h.items = [
      { id: "a1", category: "UPDATE", title: "공지제목1", body: "공지본문1", pinned: true, created_at: "2026-08-07T00:00:00Z" },
    ];
    renderWithClient(<AnnouncementsPage />);
    expect(await screen.findByText("공지제목1")).toBeInTheDocument();
    expect(screen.getByText("공지본문1")).toBeInTheDocument();
    expect(screen.getByText("UPDATE")).toBeInTheDocument();
    expect(screen.queryByText("empty")).not.toBeInTheDocument();
  });
});

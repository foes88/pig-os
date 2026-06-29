import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";

import { renderWithClient } from "../test-utils";

// 역할을 테스트마다 바꾸기 위해 hoisted 가변 홀더 사용(vi.mock 팩토리에서 참조).
const h = vi.hoisted(() => ({ role: "FARM_WORKER" }));

vi.mock("@/store/auth.store", () => ({
  useAuthStore: (sel: (s: { activeFarmId: string | null; user: { role: string } }) => unknown) =>
    sel({ activeFarmId: "farm-1", user: { role: h.role } }),
}));
vi.mock("@/lib/api/endpoints/feed", () => ({
  feedApi: {
    list: vi.fn().mockResolvedValue([
      { id: "f1", record_date: "2026-06-01", feed_type: "비육", quantity_kg: 1200 },
    ]),
    create: vi.fn(),
    delete: vi.fn(),
  },
}));

import FeedPage from "@/app/(app)/feed/page";

describe("FeedPage 권한 게이팅 (H4)", () => {
  beforeEach(() => { h.role = "FARM_WORKER"; });

  it("WORKER에게는 삭제 버튼이 보이지 않는다 (백엔드 DELETE는 MANAGE 전용)", async () => {
    h.role = "FARM_WORKER";
    renderWithClient(<FeedPage />);
    // 레코드는 로드되어 표시됨
    expect(await screen.findByText("1200")).toBeInTheDocument();
    // 삭제 버튼(t("delete") → 키 "delete")은 없어야 함
    expect(screen.queryByText("delete")).not.toBeInTheDocument();
  });

  it("OWNER에게는 삭제 버튼이 보인다", async () => {
    h.role = "FARM_OWNER";
    renderWithClient(<FeedPage />);
    expect(await screen.findByText("1200")).toBeInTheDocument();
    expect(screen.getByText("delete")).toBeInTheDocument();
  });

  it("VIEWER에게는 입력 폼과 삭제 버튼 모두 없다", async () => {
    h.role = "VIEWER";
    renderWithClient(<FeedPage />);
    expect(await screen.findByText("1200")).toBeInTheDocument();
    expect(screen.queryByText("delete")).not.toBeInTheDocument();
    // 입력 폼 추가 버튼(t("add"))도 없음 (canEntry=false)
    expect(screen.queryByText("add")).not.toBeInTheDocument();
  });
});

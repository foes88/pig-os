import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent, waitFor } from "@testing-library/react";
import { renderWithClient } from "../test-utils";

// next-intl 전역 mock. auth/chat만 개별 mock.
const h = vi.hoisted(() => ({
  activeFarmId: "farm-1" as string | null,
  query: vi.fn(() => Promise.resolve({
    intent: "explain_psy", severity: "NORMAL", answer: "AI답변입니다",
    findings: [], farm_id: "farm-1", as_of: "2026-08-07", renderer: "template",
  })),
}));
vi.mock("@/store/auth.store", () => ({
  useAuthStore: (sel: (s: { activeFarmId: string | null }) => unknown) => sel({ activeFarmId: h.activeFarmId }),
}));
vi.mock("@/lib/api/endpoints/chat", () => ({
  chatApi: { query: h.query },
}));

import ChatPage from "@/app/(app)/chat/page";

describe("ChatPage (Q&A)", () => {
  beforeEach(() => {
    h.activeFarmId = "farm-1";
    h.query.mockClear();
    // jsdom 미구현 — 메시지 추가 시 자동 스크롤 호출 스텁
    window.HTMLElement.prototype.scrollIntoView = vi.fn();
  });

  it("농장 미선택 시 선택 안내", () => {
    h.activeFarmId = null;
    renderWithClient(<ChatPage />);
    expect(screen.getByText("selectFarm")).toBeInTheDocument();
  });

  it("질문 입력·전송 → chatApi.query 호출 + 사용자 말풍선·AI 답변 렌더", async () => {
    renderWithClient(<ChatPage />);
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "PSY 왜 낮아?" } });
    fireEvent.click(screen.getByText("send"));
    // 사용자 말풍선 즉시
    expect(screen.getByText("PSY 왜 낮아?")).toBeInTheDocument();
    // 서버 호출
    await waitFor(() =>
      expect(h.query).toHaveBeenCalledWith("farm-1", expect.objectContaining({ question: "PSY 왜 낮아?" })),
    );
    // AI 답변
    expect(await screen.findByText("AI답변입니다")).toBeInTheDocument();
  });
});

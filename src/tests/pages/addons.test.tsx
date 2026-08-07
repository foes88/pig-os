import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// next-intl 전역 mock((k)=>k) 사용 → addon 이름은 t(`n_${key}`) 키로 렌더.
import AddonsPage from "@/app/(app)/addons/page";

describe("AddonsPage 카테고리 필터", () => {
  it("기본 all: 여러 카테고리 애드온 모두 표시", () => {
    render(<AddonsPage />);
    expect(screen.getByText("n_aiInsight")).toBeInTheDocument();  // analytics
    expect(screen.getByText("n_autoTask")).toBeInTheDocument();   // ops
    expect(screen.getByText("n_iot")).toBeInTheDocument();        // iot
  });

  it("analytics 탭 → analytics만, 타 카테고리 숨김", () => {
    render(<AddonsPage />);
    fireEvent.click(screen.getByText("catAnalytics"));
    expect(screen.getByText("n_aiInsight")).toBeInTheDocument();      // analytics 유지
    expect(screen.getByText("n_export")).toBeInTheDocument();         // analytics
    expect(screen.queryByText("n_autoTask")).not.toBeInTheDocument(); // ops 숨김
    expect(screen.queryByText("n_iot")).not.toBeInTheDocument();      // iot 숨김
  });

  it("iot 탭 → iot 애드온만", () => {
    render(<AddonsPage />);
    fireEvent.click(screen.getByText("catIot"));
    expect(screen.getByText("n_iot")).toBeInTheDocument();
    expect(screen.queryByText("n_aiInsight")).not.toBeInTheDocument();
  });
});

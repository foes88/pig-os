import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QuickInputDrawer } from "@/components/QuickInputDrawer";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));

describe("QuickInputDrawer", () => {
  it("renders nothing when closed", () => {
    const { container } = render(<QuickInputDrawer open={false} onClose={() => {}} />);
    expect(container.firstChild).toBeNull();
  });

  it("shows the title and subtitle when open", () => {
    render(<QuickInputDrawer open onClose={() => {}} lang="ko" />);
    expect(screen.getByText("빠른 입력")).toBeInTheDocument();
    expect(screen.getByText("이벤트 유형을 선택하세요")).toBeInTheDocument();
  });

  it("renders the core event buttons", () => {
    render(<QuickInputDrawer open onClose={() => {}} lang="ko" />);
    for (const label of ["교배", "분만", "이유", "비육돈", "양자"]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });
});

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QuickInputDrawer } from "@/components/QuickInputDrawer";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));

describe("QuickInputDrawer", () => {
  it("renders nothing when closed", () => {
    const { container } = render(<QuickInputDrawer open={false} onClose={() => {}} />);
    expect(container.firstChild).toBeNull();
  });

  // 라벨은 messages 파일 단일소스(next-intl은 setup에서 key 반환 mock) → key로 렌더 검증.
  it("shows the title and subtitle when open", () => {
    render(<QuickInputDrawer open onClose={() => {}} />);
    expect(screen.getByText("title")).toBeInTheDocument();
    expect(screen.getByText("sub")).toBeInTheDocument();
  });

  it("renders the core event buttons", () => {
    render(<QuickInputDrawer open onClose={() => {}} />);
    for (const key of ["ev_mating", "ev_farrowing", "ev_weaning", "ev_finisher", "ev_foster"]) {
      expect(screen.getByText(key)).toBeInTheDocument();
    }
  });
});

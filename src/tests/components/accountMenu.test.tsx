import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Topbar } from "@/components/Topbar";

// next-intl·next/navigation 은 setup 전역 mock(t = 키 그대로). auth/FarmSwitcher 만 개별 mock.
const h = vi.hoisted(() => ({
  replace: vi.fn(),
  clearAuth: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: h.replace, push: vi.fn() }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({}),
}));

vi.mock("@/store/auth.store", () => ({
  useAuthStore: (sel: (s: unknown) => unknown) =>
    sel({
      user: { name: "김대표", username: "admin", email: "admin@pigos.io" },
      clearAuth: h.clearAuth,
      activeFarmId: "f1",
    }),
}));

vi.mock("@/components/FarmSwitcher", () => ({ FarmSwitcher: () => <div /> }));

describe("Topbar 계정 메뉴 — 로그아웃 접근성", () => {
  beforeEach(() => {
    h.replace.mockClear();
    h.clearAuth.mockClear();
    document.cookie = "pigos_session=x; path=/";
  });

  it("★ 로그아웃이 상단바에서 한 번 눌러 닿는다(설정 페이지로 안 들어가도 됨)", () => {
    render(<Topbar />);
    fireEvent.click(screen.getByTestId("account-menu"));
    expect(screen.getByTestId("logout-button")).toBeInTheDocument();
  });

  it("사용자 이름·이메일을 보여준다 — 누구로 로그인했는지 확인 가능", () => {
    render(<Topbar />);
    // 이름은 버튼 라벨에도 나오므로 메뉴를 열기 전/후 개수로 확인한다.
    expect(screen.getAllByText("김대표")).toHaveLength(1);
    fireEvent.click(screen.getByTestId("account-menu"));
    expect(screen.getAllByText("김대표")).toHaveLength(2);   // 버튼 + 드롭다운 헤더
    expect(screen.getByText("admin@pigos.io")).toBeInTheDocument();
  });

  it("★ 한 번 눌러서는 로그아웃되지 않는다 — 확인 단계가 오클릭을 막는다", () => {
    render(<Topbar />);
    fireEvent.click(screen.getByTestId("account-menu"));
    fireEvent.click(screen.getByTestId("logout-button"));
    expect(h.clearAuth).not.toHaveBeenCalled();
    expect(h.replace).not.toHaveBeenCalled();
    expect(screen.getByTestId("logout-confirm")).toBeInTheDocument();
  });

  it("확인을 누르면 세션을 지우고 로그인으로 보낸다", () => {
    render(<Topbar />);
    fireEvent.click(screen.getByTestId("account-menu"));
    fireEvent.click(screen.getByTestId("logout-button"));
    fireEvent.click(screen.getByTestId("logout-confirm"));
    expect(h.clearAuth).toHaveBeenCalledTimes(1);
    expect(h.replace).toHaveBeenCalledWith("/login");
    expect(document.cookie).not.toContain("pigos_session=x");
  });

  it("취소하면 로그아웃되지 않고 메뉴로 돌아온다", () => {
    render(<Topbar />);
    fireEvent.click(screen.getByTestId("account-menu"));
    fireEvent.click(screen.getByTestId("logout-button"));
    fireEvent.click(screen.getByText("cancel"));   // 전역 mock 이 키를 그대로 반환
    expect(h.clearAuth).not.toHaveBeenCalled();
    expect(screen.getByTestId("logout-button")).toBeInTheDocument();
  });

  it("ESC 로 메뉴가 닫힌다 — 열어둔 채 화면을 가리지 않게", () => {
    render(<Topbar />);
    fireEvent.click(screen.getByTestId("account-menu"));
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByTestId("logout-button")).not.toBeInTheDocument();
  });
});

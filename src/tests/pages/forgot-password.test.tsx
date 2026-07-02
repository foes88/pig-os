import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";

import { renderWithClient } from "../test-utils";

// useSearchParams의 token 유무로 모드 분기 → 테스트별로 제어.
let mockSearch = "";
vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(mockSearch),
  useRouter: () => ({ replace: vi.fn(), push: vi.fn(), prefetch: vi.fn() }),
  usePathname: () => "/forgot-password",
}));
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));
vi.mock("@/lib/api/endpoints/auth", () => ({
  authApi: {
    requestPasswordReset: vi.fn().mockResolvedValue({}),
    confirmPasswordReset: vi.fn().mockResolvedValue({}),
  },
}));

import ForgotPasswordPage from "@/app/(auth)/forgot-password/page";

describe("ForgotPasswordPage (A: 비번찾기 배선)", () => {
  beforeEach(() => { mockSearch = ""; });

  it("요청 모드(토큰 없음): 이메일 입력 + 전송 버튼 렌더", () => {
    mockSearch = "";
    renderWithClient(<ForgotPasswordPage />);
    expect(screen.getByPlaceholderText("you@farm.com")).toBeInTheDocument();
    expect(screen.getByText("Send reset link")).toBeInTheDocument();
  });

  it("확인 모드(?token=): 새 비밀번호 입력 렌더", () => {
    mockSearch = "token=abc123";
    renderWithClient(<ForgotPasswordPage />);
    expect(screen.getByText("New password")).toBeInTheDocument();
    expect(screen.getByText("Confirm password")).toBeInTheDocument();
  });
});

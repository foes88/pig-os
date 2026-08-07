import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// /legal 은 t.raw(tab)로 조항 배열을 읽음 → 전역 mock((k)=>k)엔 .raw 없어 이 파일만 오버라이드.
vi.mock("next-intl", () => {
  const t = ((k: string) => k) as ((k: string) => string) & { raw: (k: string) => unknown };
  t.raw = (k: string) =>
    k === "terms"
      ? [{ h: "TERMS_H1", b: "TERMS_B1" }]
      : [{ h: "PRIVACY_H1", b: "PRIVACY_B1" }];
  return { useTranslations: () => t, useLocale: () => "en" };
});

import LegalPage from "@/app/(app)/legal/page";

describe("LegalPage (약관/방침 뷰어)", () => {
  it("기본 탭=약관: 제목·면책·탭·약관 조항 렌더", () => {
    render(<LegalPage />);
    expect(screen.getByText("title")).toBeInTheDocument();
    expect(screen.getByText("disclaimer")).toBeInTheDocument();
    expect(screen.getByText("tabTerms")).toBeInTheDocument();
    expect(screen.getByText("tabPrivacy")).toBeInTheDocument();
    expect(screen.getByText("TERMS_H1")).toBeInTheDocument();
    expect(screen.getByText("TERMS_B1")).toBeInTheDocument();
  });

  it("방침 탭 클릭 → 방침 조항으로 전환", () => {
    render(<LegalPage />);
    expect(screen.queryByText("PRIVACY_H1")).not.toBeInTheDocument();
    fireEvent.click(screen.getByText("tabPrivacy"));
    expect(screen.getByText("PRIVACY_H1")).toBeInTheDocument();
    expect(screen.queryByText("TERMS_H1")).not.toBeInTheDocument();
  });
});

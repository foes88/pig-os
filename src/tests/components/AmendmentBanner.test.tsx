import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent, waitFor } from "@testing-library/react";
import { renderWithClient } from "../test-utils";

// next-intl/next-navigation은 setup 전역 mock((k)=>k). auth/consent/farms만 개별 mock.
const h = vi.hoisted(() => ({
  activeFarmId: "f1" as string | null,
  accessToken: "tok" as string | null,
  farms: [{ id: "f1", country: "KR" }] as { id: string; country: string }[],
  current: [{ notice_version: "MASTER_TERMS@0.1" }] as { notice_version: string | null }[],
  planVersion: "MASTER_TERMS@0.2",
}));

vi.mock("@/store/auth.store", () => ({
  useAuthStore: (sel: (s: { activeFarmId: string | null; accessToken: string | null }) => unknown) =>
    sel({ activeFarmId: h.activeFarmId, accessToken: h.accessToken }),
}));
vi.mock("@/lib/api/endpoints/farms", () => ({
  farmsApi: { list: vi.fn(() => Promise.resolve(h.farms)) },
}));
vi.mock("@/lib/api/endpoints/consent", () => ({
  consentApi: {
    current: vi.fn(() => Promise.resolve(h.current)),
    signupPlan: vi.fn(() => Promise.resolve({ notice_version: h.planVersion })),
  },
}));

import AmendmentBanner from "@/components/consent/AmendmentBanner";

describe("AmendmentBanner (개정 재고지)", () => {
  beforeEach(() => {
    h.activeFarmId = "f1";
    h.accessToken = "tok";
    h.farms = [{ id: "f1", country: "KR" }];
    h.current = [{ notice_version: "MASTER_TERMS@0.1" }];
    h.planVersion = "MASTER_TERMS@0.2";
  });

  it("기록 버전 != 현재 문서 버전이면 배너 노출", async () => {
    renderWithClient(<AmendmentBanner />);
    expect(await screen.findByText("amendment.title")).toBeInTheDocument();
    expect(screen.getByText("amendment.review")).toBeInTheDocument();
  });

  it("버전 일치면 아무것도 렌더 안 함(null)", async () => {
    h.planVersion = "MASTER_TERMS@0.1"; // current와 동일 → outdated=false
    renderWithClient(<AmendmentBanner />);
    await waitFor(() => expect(screen.queryByText("amendment.title")).not.toBeInTheDocument());
  });

  it("닫기 버튼 클릭 시 배너 사라짐", async () => {
    renderWithClient(<AmendmentBanner />);
    const title = await screen.findByText("amendment.title");
    expect(title).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("dismiss"));
    expect(screen.queryByText("amendment.title")).not.toBeInTheDocument();
  });
});

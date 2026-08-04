import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent, waitFor } from "@testing-library/react";
import { renderWithClient } from "../test-utils";

// 설정→데이터·프라이버시: 목적별 현재상태 + 철회/제외 액션. next-intl 전역 mock((k)=>k).
const h = vi.hoisted(() => ({
  activeFarmId: "f1" as string | null,
  farms: [{ id: "f1", country: "KR" }] as { id: string; country: string }[],
  current: [
    { purpose_code: "AI_MODEL_TRAINING", consent_status: "GRANTED" },
    { purpose_code: "ANON_AGG_STATS", consent_status: "EXCLUSION_REQUESTED" },
  ] as { purpose_code: string; consent_status: string }[],
  withdraw: vi.fn(() => Promise.resolve({ purpose_code: "AI_MODEL_TRAINING", consent_status: "WITHDRAWN" })),
}));

vi.mock("@/store/auth.store", () => ({
  useAuthStore: (sel: (s: { activeFarmId: string | null }) => unknown) => sel({ activeFarmId: h.activeFarmId }),
}));
vi.mock("@/lib/api/endpoints/farms", () => ({
  farmsApi: { list: vi.fn(() => Promise.resolve(h.farms)) },
}));
vi.mock("@/lib/api/endpoints/consent", () => ({
  consentApi: {
    current: vi.fn(() => Promise.resolve(h.current)),
    withdraw: h.withdraw,
    signupPlan: vi.fn(() => Promise.resolve({
      notice_version: "MASTER_TERMS@0.1",
      purposes: [
        { purpose_code: "SERVICE_OPERATION", visible: true },
        { purpose_code: "AI_MODEL_TRAINING", visible: true },
        { purpose_code: "ANON_AGG_STATS", visible: true },
      ],
    })),
  },
}));

import DataPrivacyPage from "@/app/(app)/settings/data/page";

describe("DataPrivacyPage (설정 데이터·프라이버시)", () => {
  beforeEach(() => {
    h.activeFarmId = "f1";
    h.withdraw.mockClear();
  });

  it("visible 목적 라벨 렌더", async () => {
    renderWithClient(<DataPrivacyPage />);
    expect(await screen.findByText("purpose.SERVICE_OPERATION.label")).toBeInTheDocument();
    expect(screen.getByText("purpose.AI_MODEL_TRAINING.label")).toBeInTheDocument();
  });

  it("계약이행 목적(SERVICE_OPERATION)은 철회 불가 안내", async () => {
    renderWithClient(<DataPrivacyPage />);
    expect(await screen.findByText("action.contractRequired")).toBeInTheDocument();
  });

  it("GRANTED 옵트인은 철회 버튼 → 클릭 시 withdraw 호출", async () => {
    renderWithClient(<DataPrivacyPage />);
    const btn = await screen.findByText("action.WITHDRAWN");
    fireEvent.click(btn);
    await waitFor(() =>
      expect(h.withdraw).toHaveBeenCalledWith({ purpose_code: "AI_MODEL_TRAINING", farm_id: "f1", action: "WITHDRAWN" }),
    );
  });

  it("이미 제외요청된 목적은 액션 버튼 없음", async () => {
    renderWithClient(<DataPrivacyPage />);
    await screen.findByText("purpose.ANON_AGG_STATS.label");
    // ANON_AGG_STATS 는 EXCLUSION_REQUESTED 상태 → 액션 버튼(action.EXCLUSION_REQUESTED) 미노출
    expect(screen.queryByText("action.EXCLUSION_REQUESTED")).not.toBeInTheDocument();
  });
});

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import ConsentForm from "@/components/consent/ConsentForm";
import type { SignupPlan } from "@/types/api.types";

// next-intl은 setup에서 (k)=>k mock → 라벨은 키로 검증(타 컴포넌트 테스트 컨벤션 동일).
function plan(over: Partial<SignupPlan> = {}): SignupPlan {
  return {
    jurisdiction: { code: "KR", country: "KR", group: "KR", counsel_review: false, notes: [] },
    gate: { signup_blocked: false, paid_blocked: false, release_hold: false, reason_code: null },
    state_flags: {
      state: null, written_opt_in_required: false, do_not_sell_link: false,
      honor_uoom: false, exclude_location_from_sale: false,
    },
    documents: [
      { doc_id: "MASTER_TERMS", kind: "master", version: "0.1", status: "DRAFT_LAWYER_PENDING",
        lang: "en", is_legal_priority: true, lang_pending: false, body: null },
    ],
    notice_version: "MASTER_TERMS@0.1",
    any_draft: true,
    lang_gate: false,
    required_acks: ["TERMS", "PRIVACY"],
    purposes: [
      { purpose_code: "SERVICE_OPERATION", order: 0, ui_kind: "NOTICE", lawful_basis: "CONTRACT",
        visible: true, is_toggle: false, default_on: false, requires_evidence: false,
        status_tag: "LEGAL_REQUIREMENT", auto_off_if_uoom: false },
      { purpose_code: "AI_MODEL_TRAINING", order: 2, ui_kind: "OPT_IN", lawful_basis: "CONSENT",
        visible: true, is_toggle: true, default_on: false, requires_evidence: true,
        status_tag: "LEGAL_REQUIREMENT", auto_off_if_uoom: false },
    ],
    lang: "en",
    ...over,
  };
}

describe("ConsentForm", () => {
  it("가입 모드: 문서·필수2체크·목적·제출 렌더", () => {
    render(<ConsentForm plan={plan()} mode="signup" onSubmit={() => {}} />);
    expect(screen.getByText(/documentsTitle/)).toBeInTheDocument();  // notice_version과 한 <p>라 부분매칭
    expect(screen.getByText("ack.terms")).toBeInTheDocument();
    expect(screen.getByText("ack.privacy")).toBeInTheDocument();
    expect(screen.getByText("purpose.SERVICE_OPERATION.label")).toBeInTheDocument();
    expect(screen.getByText("purpose.AI_MODEL_TRAINING.label")).toBeInTheDocument();
    expect(screen.getByText("submit.signup")).toBeInTheDocument();
  });

  it("차단 법역(CN)은 blocked 화면·제출 없음", () => {
    const blocked = plan({ gate: { signup_blocked: true, paid_blocked: false, release_hold: false, reason_code: "HOLD_D07" } });
    render(<ConsentForm plan={blocked} mode="signup" onSubmit={() => {}} />);
    expect(screen.getByText("blocked.title")).toBeInTheDocument();
    expect(screen.queryByText("submit.signup")).not.toBeInTheDocument();
  });

  it("embedded 모드: 자체 제출버튼 없음 + onChange 방출", () => {
    const onChange = vi.fn();
    render(<ConsentForm plan={plan()} mode="signup" embedded onChange={onChange} />);
    expect(screen.queryByText("submit.signup")).not.toBeInTheDocument();
    expect(onChange).toHaveBeenCalled();
    // 초기 방출: 필수 미체크라 canSubmit=false
    const last = onChange.mock.calls.at(-1)![0];
    expect(last.canSubmit).toBe(false);
  });

  it("DRAFT 배너: any_draft면 draft 안내 노출", () => {
    render(<ConsentForm plan={plan({ any_draft: true })} mode="signup" onSubmit={() => {}} />);
    expect(screen.getByText("banner.draft")).toBeInTheDocument();
  });
});

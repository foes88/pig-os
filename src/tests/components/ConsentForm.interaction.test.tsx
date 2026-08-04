import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ConsentForm from "@/components/consent/ConsentForm";
import type { SignupPlan } from "@/types/api.types";

// canSubmit 전이: 가입은 필수 2체크 후 true, 설정(settings)은 ack 불요로 즉시 true.
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
    ],
    lang: "en",
    ...over,
  };
}

describe("ConsentForm 상호작용 (canSubmit 전이)", () => {
  it("가입: 필수 2체크 전 false → 둘 다 체크하면 true", () => {
    const onChange = vi.fn();
    render(<ConsentForm plan={plan()} mode="signup" embedded onChange={onChange} />);
    // 초기: 미체크 → false
    expect(onChange.mock.calls.at(-1)![0].canSubmit).toBe(false);
    const boxes = screen.getAllByRole("checkbox");
    fireEvent.click(boxes[0]); // terms
    fireEvent.click(boxes[1]); // privacy
    expect(onChange.mock.calls.at(-1)![0].canSubmit).toBe(true);
  });

  it("설정 모드: ack 없이도 canSubmit true", () => {
    const onChange = vi.fn();
    render(<ConsentForm plan={plan()} mode="settings" embedded onChange={onChange} />);
    expect(onChange.mock.calls.at(-1)![0].canSubmit).toBe(true);
  });

  it("가입 차단 법역이면 체크해도 canSubmit false 유지", () => {
    const onChange = vi.fn();
    const blocked = plan({ gate: { signup_blocked: true, paid_blocked: false, release_hold: false, reason_code: "HOLD_D07" } });
    render(<ConsentForm plan={blocked} mode="settings" embedded onChange={onChange} />);
    expect(onChange.mock.calls.at(-1)![0].canSubmit).toBe(false);
  });
});

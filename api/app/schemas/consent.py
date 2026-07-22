"""동의 인프라 스키마 (CONSENT_SPEC §3~§5, TERMS_DISPLAY §4·§7)."""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocMeta(BaseModel):
    doc_id: str
    kind: str
    version: str
    status: str
    lang: str
    is_legal_priority: bool
    lang_pending: bool
    body: str | None = None


class PurposePlan(BaseModel):
    purpose_code: str
    order: int
    ui_kind: str            # NOTICE | NOTICE_EXCLUSION | LI_OBJECT | OPT_IN | WRITTEN_OPT_IN | HIDDEN | TRANSFER_CONSENT | BLOCKED
    lawful_basis: str
    visible: bool           # 화면 노출 여부(HIDDEN/BLOCKED=false)
    is_toggle: bool         # 사용자 개별 토글(옵트인) 여부
    default_on: bool = False
    requires_evidence: bool = False
    status_tag: str
    auto_off_if_uoom: bool = False   # ⑤: UOOM 신호 시 강제 OFF


class GateOut(BaseModel):
    signup_blocked: bool = False
    paid_blocked: bool = False
    release_hold: bool = False
    reason_code: str | None = None


class StateFlagsOut(BaseModel):
    state: str | None = None
    written_opt_in_required: bool = False
    do_not_sell_link: bool = False
    honor_uoom: bool = False
    exclude_location_from_sale: bool = False


class JurisdictionOut(BaseModel):
    code: str
    country: str
    group: str
    counsel_review: bool = False
    notes: list[str] = Field(default_factory=list)


class SignupPlan(BaseModel):
    """가입 동의 화면을 그리는 데 필요한 전부. 프론트는 이걸로 UI 구성."""
    jurisdiction: JurisdictionOut
    gate: GateOut
    state_flags: StateFlagsOut
    documents: list[DocMeta]
    notice_version: str
    any_draft: bool
    lang_gate: bool
    required_acks: list[str]          # ['TERMS', 'PRIVACY'] — 필수 2체크
    purposes: list[PurposePlan]
    lang: str


class ConsentChoice(BaseModel):
    purpose_code: str
    granted: bool = False
    evidence_ref: str | None = None   # 서면·전자서명 증적(NE 등)


class RecordConsentRequest(BaseModel):
    farm_id: UUID | None = None
    selected_country: str
    farm_country: str | None = None
    farm_state: str | None = None
    lang: str | None = None
    terms_ack: bool = False
    privacy_ack: bool = False
    choices: list[ConsentChoice] = Field(default_factory=list)
    collection_context: str = "UI_SIGNUP"


class ConsentStatusOut(BaseModel):
    purpose_code: str
    jurisdiction: str
    lawful_basis: str
    consent_status: str
    notice_version: str
    accepted_at: datetime | None = None
    withdrawn_at: datetime | None = None
    effective_from: date | None = None
    collection_context: str


class WithdrawRequest(BaseModel):
    purpose_code: str
    farm_id: UUID | None = None
    # WITHDRAWN(옵트인 철회) | OBJECTED(LI 이의) | EXCLUSION_REQUESTED(익명 편입 제외)
    action: str = "WITHDRAWN"
    reason: str | None = None

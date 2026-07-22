"""동의·데이터이용 원장 (consent_ledger).

CONSENT_AND_DATA_USE_SPEC §5.1 스키마 구현. 변호사 확정 전이라 문구/코호트 등
미결값은 이 테이블이 아니라 콘텐츠·설정 파일에서 주입한다(여기엔 상태·근거·버전만 기록).

핵심 불변식(§5.2):
- (user_id, farm_id, purpose_code) 최신 1행 = 현재 유효 상태
- lawful_basis=CONSENT 인데 evidence_ref 가 비면 무효(서면·전자서명 요구 목적은 evidence 필수)
- 기록은 append-only 지향(정정도 새 행). 이력 보존이 감사·집행 대응의 근거.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# --- enum 값 (문자열 컬럼 + CheckConstraint 로 강제; DB enum 타입은 마이그레이션 유연성 위해 미사용) ---

PURPOSE_CODES = (
    "SERVICE_OPERATION",      # ① 서비스 운영(계약 이행)
    "ANON_AGG_STATS",         # ② 익명·집계 통계/벤치마크 (국가별 분기, D-01)
    "AI_MODEL_TRAINING",      # ③ AI 모델 학습 (옵트인 D-02)
    "NAMED_RESEARCH",         # ④ 기명 연구 협력 (옵트인 D-02)
    "TRANSACTION_MATCHING",   # ⑤ 거래·리드 매칭 (옵트인 D-02, VN 미노출)
    "EXTERNAL_AI_PROCESSING", # ⑥ 외부 AI 처리(프로세서·국외이전)
)

LAWFUL_BASES = (
    "CONTRACT",              # 계약 이행
    "CONSENT",               # 동의 (evidence_ref 필수)
    "LEGITIMATE_INTEREST",   # 정당한 이익 (LIA 문서 + 이의권)
    "ANONYMIZED_EXEMPT",     # 익명정보 법적용 제외 (KR 제58조의2 등)
    "DEIDENTIFIED_EXEMPT",   # 비식별 제외 (US de-identified)
    "PROCESSOR_TRANSFER",    # 프로세서 위탁·국외이전
)

CONSENT_STATUSES = (
    "GRANTED",               # 동의함
    "NOTICE_GIVEN",          # 고지함(토글 아님 — LI/익명 고지형)
    "WITHDRAWN",             # 철회
    "OBJECTED",              # 이의(LI opt-out)
    "EXCLUSION_REQUESTED",   # 제외 요청(익명 편입 제외)
    "EXPIRED",               # 만료(재동의 필요)
)

COLLECTION_CONTEXTS = (
    "UI_SIGNUP",
    "UI_SETTINGS",
    "UI_JIT",                # just-in-time 프롬프트
    "API",
    "MIGRATION",
)


def _in(col: str, values: tuple[str, ...]) -> str:
    joined = ", ".join(f"'{v}'" for v in values)
    return f"{col} IN ({joined})"


class ConsentRecord(Base):
    """동의/고지 1건. append-only 이력 테이블."""

    __tablename__ = "consent_ledger"
    __table_args__ = (
        CheckConstraint(_in("purpose_code", PURPOSE_CODES), name="ck_consent_purpose"),
        CheckConstraint(_in("lawful_basis", LAWFUL_BASES), name="ck_consent_basis"),
        CheckConstraint(_in("consent_status", CONSENT_STATUSES), name="ck_consent_status"),
        CheckConstraint(_in("collection_context", COLLECTION_CONTEXTS), name="ck_consent_context"),
        # CONSENT 근거인데 증적 없으면 무효(§5.2)
        CheckConstraint(
            "lawful_basis <> 'CONSENT' OR evidence_ref IS NOT NULL",
            name="ck_consent_requires_evidence",
        ),
        Index("idx_consent_current", "user_id", "farm_id", "purpose_code", "created_at"),
        Index("idx_consent_farm", "farm_id", "purpose_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    # farm 단위 데이터공유 목적(②③④⑤)은 farm_id 필수, 계정 단위 목적(①⑥)은 NULL 허용
    farm_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))

    purpose_code: Mapped[str] = mapped_column(String(32), nullable=False)
    # ISO alpha-2 + US 주는 'US-NE' 형식 (법역 판별 결과)
    jurisdiction: Mapped[str] = mapped_column(String(8), nullable=False)
    lawful_basis: Mapped[str] = mapped_column(String(24), nullable=False)
    consent_status: Mapped[str] = mapped_column(String(24), nullable=False)

    # 동의 시점에 표시된 문서 버전 묶음 식별자(master@v/privacy@v/addendum@v 조합 해시나 라벨)
    notice_version: Mapped[str] = mapped_column(String(255), nullable=False)

    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_from: Mapped[date | None] = mapped_column(Date)

    # 데이터 수령 주체(익명 집계 수령자, 프로세서 등) — 고지-실제 일치(FTC §5) 근거
    downstream_recipient: Mapped[list[str] | None] = mapped_column(ARRAY(String(120)))
    collection_context: Mapped[str] = mapped_column(String(16), nullable=False, default="UI_SIGNUP")
    # 서면·전자서명 증적, 감사 로그 id, 문서 스냅샷 경로 등
    evidence_ref: Mapped[str | None] = mapped_column(Text)

    # clock_timestamp(): 같은 트랜잭션 안에서도 행마다 실제 시각 → append 순서 결정적
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )

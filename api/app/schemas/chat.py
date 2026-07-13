from uuid import UUID

from pydantic import BaseModel, Field


class ChatQuery(BaseModel):
    question: str = Field(..., min_length=2, max_length=500)
    # 공식 지원 7개국어(en/ko/zh/es/vi/th/pt). LLM 렌더러는 7개 전부 지원하나 패턴이 th/pt를
    # 누락해 태국·브라질(pt=2026-06-19 계약) 농장이 자국어 질의 시 422 → 7개로 정합(QA chat 회귀).
    locale: str = Field(default="en", pattern="^(en|ko|zh|es|vi|th|pt|ru)$")


class FindingOut(BaseModel):
    rule_id: str
    kpi: str
    severity: str
    current_value: float | None
    target_value: float | None
    causes: list[str]
    recommended_actions: list[str]


class ChatResponse(BaseModel):
    intent: str
    severity: str
    answer: str
    findings: list[FindingOut]
    farm_id: UUID
    as_of: str
    renderer: str = "template"  # "template" | "llm" — lets client know which tier responded

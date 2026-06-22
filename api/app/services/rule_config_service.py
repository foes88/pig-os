"""AI 규칙 운영 설정 로더/저장 (운영자 콘솔 Phase 3).

엔진은 build_rule_context 에서 load_rule_configs() 결과를 ctx.extra["rule_configs"]로 받는다.
행이 없으면 빈 dict → 엔진은 코드 기본값 + enabled=True 로 폴백(비파괴적).
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.rule_config import RuleConfig


async def load_rule_configs(db: AsyncSession) -> dict[str, dict]:
    """{rule_id: {"enabled": bool, "warning": float|None, "critical": float|None}}"""
    rows = (await db.execute(select(RuleConfig))).scalars().all()
    return {
        r.rule_id: {"enabled": r.enabled, "warning": r.warning, "critical": r.critical}
        for r in rows
    }

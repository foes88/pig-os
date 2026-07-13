"""운영자 어드민 — AI 규칙 설정 (Phase 3, PigOS 네이티브).

엔진 규칙(RuleRegistry)을 나열하고, 임계값·활성여부를 DB(rule_configs)로 오버라이드.
배포 없이 운영자가 조정. require_super_admin. 변경은 AuditLog.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from app.core.dependencies import DbDep, SuperAdmin, require_super_admin
from app.core.exceptions import NotFoundError, ValidationError
from app.db.models.platform import AuditLog
from app.db.models.rule_config import RuleConfig
from app.engine import RuleEngine  # noqa: F401  (ensure engine import side-effects)
from app.engine.rule_engine import RuleRegistry

# 규칙 등록 보장(임포트 부작용)
from app.engine.rules import base as _b  # noqa: F401
from app.engine.rules import batch as _bt  # noqa: F401
from app.engine.rules import boar as _bo  # noqa: F401
from app.engine.rules import composite as _cp  # noqa: F401
from app.engine.rules import disease as _d  # noqa: F401
from app.engine.rules import grow_finish as _gf  # noqa: F401
from app.engine.rules import litter as _l  # noqa: F401
from app.engine.rules import loss as _ls  # noqa: F401
from app.engine.rules import reproduction as _r  # noqa: F401
from app.engine.rules import sow_herd as _sh  # noqa: F401

router = APIRouter(
    prefix="/admin",
    tags=["Admin · Rules"],
    dependencies=[Depends(require_super_admin)],
)


class RuleRow(BaseModel):
    rule_id: str
    domain: str
    description: str
    tier: str
    enabled: bool
    warning: float | None
    critical: float | None


class RuleUpdate(BaseModel):
    enabled: bool | None = None
    warning: float | None = None
    critical: float | None = None


@router.get("/rules", response_model=list[RuleRow])
async def list_rules(db: DbDep, _admin: SuperAdmin) -> list[RuleRow]:
    """등록된 모든 규칙 + DB 오버라이드(없으면 활성·임계 null=코드기본)."""
    cfgs = {c.rule_id: c for c in (await db.execute(select(RuleConfig))).scalars().all()}
    out: list[RuleRow] = []
    for r in RuleRegistry.all():
        c = cfgs.get(r.rule_id)
        out.append(RuleRow(
            rule_id=r.rule_id, domain=r.domain, description=r.description, tier=r.tier,
            enabled=c.enabled if c else True,
            warning=c.warning if c else None,
            critical=c.critical if c else None,
        ))
    out.sort(key=lambda x: (x.tier != "base", x.domain, x.rule_id))
    return out


@router.patch("/rules/{rule_id}", response_model=RuleRow)
async def update_rule(rule_id: str, body: RuleUpdate, db: DbDep, admin: SuperAdmin) -> RuleRow:
    """규칙 활성/임계 오버라이드 upsert."""
    known = {r.rule_id: r for r in RuleRegistry.all()}
    if rule_id not in known:
        raise NotFoundError(f"Unknown rule: {rule_id}")
    # 임계 순서(warning<critical)는 방향에 따라 달라진다 — below형(PSY/분만율)은 warning>critical이 정상.
    # 방향은 벤치마크(국가)에서 런타임 결정되어 규칙에 정적으로 없으므로, 여기선 동일값만 거부한다.
    # (심각도 판정은 rule engine의 _severity_from_bench가 방향-인지로 처리)
    if body.warning is not None and body.critical is not None and body.warning == body.critical:
        raise ValidationError("warning and critical must differ")

    cfg = await db.get(RuleConfig, rule_id)
    if not cfg:
        cfg = RuleConfig(rule_id=rule_id, enabled=True)
        db.add(cfg)
    before = {"enabled": cfg.enabled, "warning": cfg.warning, "critical": cfg.critical}
    # ADM-RULES-NULLCLEAR: model_fields_set으로 '전달됨(명시적 null 포함)'과 '누락'을 구분 →
    # warning/critical을 null로 보내면 코드 기본값으로 클리어 가능(과거엔 is_not_none이라 불가).
    fields = body.model_fields_set
    if body.enabled is not None:
        cfg.enabled = body.enabled
    if "warning" in fields:
        cfg.warning = body.warning
    if "critical" in fields:
        cfg.critical = body.critical
    cfg.updated_by = admin.id

    db.add(AuditLog(
        user_id=admin.id, action="UPDATE", entity_type="rule_config",
        old_value={k: str(v) for k, v in before.items()},
        new_value={"enabled": str(cfg.enabled), "warning": str(cfg.warning), "critical": str(cfg.critical)},
    ))
    await db.commit()
    await db.refresh(cfg)

    r = known[rule_id]
    return RuleRow(
        rule_id=r.rule_id, domain=r.domain, description=r.description, tier=r.tier,
        enabled=cfg.enabled, warning=cfg.warning, critical=cfg.critical,
    )

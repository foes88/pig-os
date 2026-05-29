from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.config import FarmConfig
from app.db.models.platform import Farm, Organization, UserFarm
from app.db.models.sow import Building, Sow
from app.schemas.farm import FarmConfigSet, FarmCreate, FarmResponse, FarmUpdate, OnboardingStatus


def _generate_farm_code(country: str, org_id: UUID) -> str:
    suffix = str(org_id)[:6].upper()
    return f"FARM-{country.upper()}-{suffix}"


async def create_farm(
    db: AsyncSession,
    org_id: UUID,
    user_id: UUID,
    req: FarmCreate,
) -> Farm:
    farm = Farm(
        org_id=org_id,
        farm_code=_generate_farm_code(req.country, org_id),
        **req.model_dump(),
    )
    db.add(farm)
    await db.flush()

    db.add(UserFarm(user_id=user_id, farm_id=farm.id, role_override="FARM_OWNER"))
    await db.commit()
    await db.refresh(farm)
    return farm


async def list_farms(db: AsyncSession, user_id: UUID) -> list[Farm]:
    rows = await db.scalars(
        select(Farm)
        .join(UserFarm, UserFarm.farm_id == Farm.id)
        .where(UserFarm.user_id == user_id, Farm.active.is_(True))
        .order_by(Farm.created_at)
    )
    return list(rows)


async def update_farm(db: AsyncSession, farm: Farm, req: FarmUpdate) -> Farm:
    for k, v in req.model_dump(exclude_none=True).items():
        setattr(farm, k, v)
    await db.commit()
    await db.refresh(farm)
    return farm


async def set_farm_configs(db: AsyncSession, farm_id: UUID, req: FarmConfigSet) -> list[FarmConfig]:
    """Upsert farm configs from onboarding payload."""
    key_map = {
        "gestation_days": "GESTATION_DAYS",
        "lactation_days": "LACTATION_DAYS",
        "wei_target_days": "WEI_TARGET_DAYS",
        "pregnancy_check_day": "PREGNANCY_CHECK_DAY",
        "npd_alert_threshold": "NPD_ALERT_THRESHOLD",
        "sow_cull_parity_threshold": "SOW_CULL_PARITY_THRESHOLD",
    }
    results = []
    for field, key in key_map.items():
        value = getattr(req, field)
        if value is None:
            continue
        existing = await db.scalar(
            select(FarmConfig).where(
                FarmConfig.farm_id == farm_id,
                FarmConfig.config_key == key,
            )
        )
        if existing:
            existing.config_value = str(value)
            results.append(existing)
        else:
            cfg = FarmConfig(farm_id=farm_id, config_key=key, config_value=str(value))
            db.add(cfg)
            results.append(cfg)
    await db.commit()
    return results


async def get_onboarding_status(db: AsyncSession, farm_id: UUID) -> OnboardingStatus:
    config_count = await db.scalar(
        select(func.count()).select_from(FarmConfig).where(FarmConfig.farm_id == farm_id)
    )
    sow_count = await db.scalar(
        select(func.count()).select_from(Sow).where(Sow.farm_id == farm_id, Sow.deleted_at.is_(None))
    )
    building_count = await db.scalar(
        select(func.count()).select_from(Building).where(Building.farm_id == farm_id)
    )

    has_farm_config = (config_count or 0) > 0
    has_sows = (sow_count or 0) > 0
    has_buildings = (building_count or 0) > 0

    checks = [has_farm_config, has_sows, has_buildings]
    pct = int(sum(checks) / len(checks) * 100)

    return OnboardingStatus(
        farm_id=farm_id,
        has_farm_config=has_farm_config,
        has_sows=has_sows,
        has_buildings=has_buildings,
        onboarding_complete=all(checks),
        completion_pct=pct,
    )

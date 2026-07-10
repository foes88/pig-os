"""Shared constants for the PigPlan pilot follow-up scripts."""
from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import UUID, uuid5

PILOT_PASSWORD_ENV = "PIGPLAN_PILOT_PASSWORD"
PILOT_API_BASE_ENV = "PIGPLAN_PILOT_API_BASE"

PILOT_FARMS = (2807, 4448, 848, 978)
EAST_FARMS = (2807, 4448)
WEST_FARMS = (848, 978)

# Fixed UUID namespace for idempotent pilot setup.
NS = "a11c0000"


def farm_uuid(farm_no: int) -> UUID:
    return UUID(f"{NS}-0000-0000-0000-{farm_no:012d}")


def farm_uuid_str(farm_no: int) -> str:
    return str(farm_uuid(farm_no))


# 계정 태그(vadmin/deast 등 비-hex) → 결정론적 UUID(uuid5). 멱등·유효 UUID 보장.
_USER_NS = UUID(f"{NS}-0000-0000-00a1-000000000000")


def user_uuid(tag: str) -> UUID:
    return uuid5(_USER_NS, tag)


VENDOR = UUID(f"{NS}-0000-0000-00b0-000000000001")
DEALER_E = UUID(f"{NS}-0000-0000-00b0-000000000002")
DEALER_W = UUID(f"{NS}-0000-0000-00b0-000000000003")

ORG_SPECS = (
    (VENDOR, "VENDOR", "피그플랜 시범사업단", None, 0),
    (DEALER_E, "DEALER", "동부지사", VENDOR, 2),
    (DEALER_W, "DEALER", "서부지사", VENDOR, 2),
)
FARM_ORG = {2807: DEALER_E, 4448: DEALER_E, 848: DEALER_W, 978: DEALER_W}


@dataclass(frozen=True)
class AccountSpec:
    uuid_tag: str
    username: str
    system_role: str
    org_id: UUID
    farm_no: int | None
    expected_farms: tuple[int, ...]
    denied_farm: int | None

    @property
    def expected_farm_ids(self) -> set[str]:
        return {farm_uuid_str(farm_no) for farm_no in self.expected_farms}


ACCOUNTS = (
    AccountSpec("vadmin", "vendor_admin", "VENDOR_ADMIN", VENDOR, None, PILOT_FARMS, None),
    AccountSpec("deast", "dealer_east", "DEALER_ADMIN", DEALER_E, None, EAST_FARMS, 848),
    AccountSpec("dwest", "dealer_west", "DEALER_ADMIN", DEALER_W, None, WEST_FARMS, 2807),
    AccountSpec("ow2807", "owner_2807", "FARM_OWNER", DEALER_E, 2807, (2807,), 4448),
    AccountSpec("ow4448", "owner_4448", "FARM_OWNER", DEALER_E, 4448, (4448,), 2807),
    AccountSpec("ow848", "owner_848", "FARM_OWNER", DEALER_W, 848, (848,), 978),
    AccountSpec("ow978", "owner_978", "FARM_OWNER", DEALER_W, 978, (978,), 848),
)


def get_pilot_password() -> str:
    password = os.getenv(PILOT_PASSWORD_ENV)
    if not password:
        raise RuntimeError(
            f"{PILOT_PASSWORD_ENV} is required for pilot account setup/UAT. "
            "Set it to the documented pilot password before running Phase A or B."
        )
    return password

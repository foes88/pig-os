"""
Devices router — 모바일 푸시 토큰 등록/해제 (G2).

유저 스코프. 로그인 직후 토큰 등록, 로그아웃 시 해제.
"""
from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbDep
from app.schemas.device import DeviceRegister, DeviceResponse
from app.services import device_service

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post("", response_model=DeviceResponse, status_code=201)
async def register_device(body: DeviceRegister, user: CurrentUser, db: DbDep) -> DeviceResponse:
    device = await device_service.register_device(
        db, user.id, body.platform, body.token, body.app_version,
    )
    return DeviceResponse.model_validate(device)


@router.get("", response_model=list[DeviceResponse])
async def list_devices(user: CurrentUser, db: DbDep) -> list[DeviceResponse]:
    rows = await device_service.list_user_devices(db, user.id)
    return [DeviceResponse.model_validate(d) for d in rows]


@router.delete("/{token}", status_code=204)
async def unregister_device(token: str, user: CurrentUser, db: DbDep) -> None:
    await device_service.unregister_token(db, user.id, token)

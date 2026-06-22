"""운영자 어드민 콘솔 라우터 (SUPER_ADMIN 전용, 전사 스코프).

테넌트(/farms/{farm_id}) 스코프가 아니라 플랫폼 운영자가 전사를 관리하는 백오피스.
모든 엔드포인트는 require_super_admin 으로 보호된다.
"""
from app.routers.admin.admin import router as admin_router

__all__ = ["admin_router"]

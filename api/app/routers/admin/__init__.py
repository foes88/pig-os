"""운영자 어드민 콘솔 라우터 (SUPER_ADMIN 전용, 전사 스코프).

테넌트(/farms/{farm_id}) 스코프가 아니라 플랫폼 운영자가 전사를 관리하는 백오피스.
모든 엔드포인트는 require_super_admin 으로 보호된다.
하위 모듈: admin(overview/me) · users(회원/베타가입) · content(공지/문의, Phase 2) ...
"""
from app.routers.admin.admin import router as core_router
from app.routers.admin.content import router as content_router
from app.routers.admin.rules import router as rules_router
from app.routers.admin.users import router as users_router

__all__ = ["core_router", "users_router", "content_router", "rules_router"]

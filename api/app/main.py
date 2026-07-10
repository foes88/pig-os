"""
PigOS API — FastAPI entry point.

Architecture:
  Base routers  → always mounted
  Addon routers → discovered from AddonRegistry at startup

To add a new Addon:
  1. Create app/addons/<name>/ package with AddonRegistry.register() call
  2. Import it in app/routers/addons/__init__.py
  3. Restart → router appears automatically at /addons/<url_prefix>/
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.addons import AddonRegistry
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.routers.base import (
    alerts,
    analytics,
    auth,
    boars,
    chat,
    config,
    devices,
    events,
    farms,
    feed,
    finishers,
    kpi,
    members,
    notifications,
    onboarding,
    orgs,
    piglets,
    pilot_signups,
    reports,
    sows,
    sync,
    tasks,
    thresholds,
)

# ── Import Addon packages here to trigger AddonRegistry.register() ──────────
# from app.addons import fcr      # uncomment when Addon #1 is ready
# from app.addons import health   # Addon #2
# from app.addons import market   # Addon #4
# from app.addons import breeding # Addon #5
# from app.addons import biosec   # Addon #6
# ────────────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    addons = AddonRegistry.all()
    print(f"[PigOS] {len(addons)} Addon(s) registered: {[a.code for a in addons]}")
    yield


app = FastAPI(
    title="PigOS API",
    version="0.1.0",
    description="Global Swine Farm Management — Base API + AI Addon platform",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ────────────────────────────────────────────────────────
register_exception_handlers(app)

V1 = "/api/v1"

# ── Public routers (no auth) ─────────────────────────────────────────────────
app.include_router(pilot_signups.router, prefix=V1)

# ── Base routers ─────────────────────────────────────────────────────────────
app.include_router(auth.router,        prefix=V1)
app.include_router(orgs.router,        prefix=V1)
app.include_router(onboarding.router,  prefix=V1)
app.include_router(config.router,      prefix=V1)
app.include_router(farms.router,       prefix=V1)
app.include_router(sows.router,        prefix=V1)
app.include_router(events.router,      prefix=V1)
app.include_router(kpi.router,         prefix=V1)
app.include_router(chat.router,        prefix=V1)
app.include_router(sync.router,        prefix=V1)
app.include_router(finishers.router,   prefix=V1)
app.include_router(feed.router,        prefix=V1)
app.include_router(piglets.router,     prefix=V1)
app.include_router(boars.router,       prefix=V1)
app.include_router(alerts.router,      prefix=V1)
app.include_router(tasks.router,       prefix=V1)
app.include_router(thresholds.router,  prefix=V1)
app.include_router(notifications.router, prefix=V1)
app.include_router(notifications.farm_router, prefix=V1)
app.include_router(devices.router,     prefix=V1)
app.include_router(reports.router,     prefix=V1)
app.include_router(analytics.router,   prefix=V1)
app.include_router(members.router,     prefix=V1)

# ── Admin console (SUPER_ADMIN 전용, 전사 스코프) ─────────────────────────────
from app.routers.admin import audit_router as admin_audit_router  # noqa: E402
from app.routers.admin import benchmarks_router as admin_benchmarks_router  # noqa: E402
from app.routers.admin import content_router as admin_content_router  # noqa: E402
from app.routers.admin import core_router as admin_core_router  # noqa: E402
from app.routers.admin import master_data_router as admin_master_data_router  # noqa: E402
from app.routers.admin import orgs_router as admin_orgs_router  # noqa: E402
from app.routers.admin import rules_router as admin_rules_router  # noqa: E402
from app.routers.admin import users_router as admin_users_router  # noqa: E402
from app.routers.base import announcements as base_announcements  # noqa: E402
from app.routers.base import support as base_support  # noqa: E402

app.include_router(admin_core_router,   prefix=V1)
app.include_router(admin_users_router,  prefix=V1)
app.include_router(admin_content_router, prefix=V1)
app.include_router(admin_rules_router,  prefix=V1)
app.include_router(admin_audit_router,  prefix=V1)
app.include_router(admin_orgs_router,   prefix=V1)
app.include_router(admin_benchmarks_router, prefix=V1)
app.include_router(admin_master_data_router, prefix=V1)
app.include_router(base_announcements.router, prefix=V1)
app.include_router(base_support.router, prefix=V1)

# ── Addon routers (auto-discovered from AddonRegistry) ───────────────────────
for addon in AddonRegistry.all():
    app.include_router(
        addon.router,
        prefix=f"{V1}/addons/{addon.url_prefix}",
        tags=addon.tags or [f"Addon: {addon.name}"],
    )


@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "version": app.version}

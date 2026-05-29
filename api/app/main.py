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
from app.routers.base import auth, chat, events, farms, kpi, onboarding, sows, sync

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
    allow_origins=["*"] if not settings.is_production else [
        "https://pigos.io",
        "https://app.pigos.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ────────────────────────────────────────────────────────
register_exception_handlers(app)

V1 = "/api/v1"

# ── Base routers ─────────────────────────────────────────────────────────────
app.include_router(auth.router,        prefix=V1)
app.include_router(onboarding.router,  prefix=V1)
app.include_router(farms.router,       prefix=V1)
app.include_router(sows.router,        prefix=V1)
app.include_router(events.router,      prefix=V1)
app.include_router(kpi.router,         prefix=V1)
app.include_router(chat.router,        prefix=V1)
app.include_router(sync.router,        prefix=V1)

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

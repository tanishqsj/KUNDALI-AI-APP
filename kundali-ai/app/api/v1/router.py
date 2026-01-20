from fastapi import APIRouter

from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.kundali import router as kundali_router
from app.api.v1.routes.ask import router as ask_router
from app.api.v1.routes.voice import router as voice_router
from app.api.v1.routes.report import router as report_router
from app.api.v1.routes.history import router as history_router
# If you have other routes like 'kundali', import them here too
# from app.api.v1.routes import kundali

from app.api.admin.router import router as admin_router
api_router = APIRouter()

# ─────────────────────────────────────────────
# Public Routes
# ─────────────────────────────────────────────

api_router.include_router(
    health_router,
    tags=["Health"],
)

api_router.include_router(
    kundali_router,
    tags=["Kundali"],
)

api_router.include_router(
    ask_router,
    tags=["Ask"],
)

api_router.include_router(voice_router, prefix="/voice", tags=["Voice"])
api_router.include_router(report_router, prefix="/report", tags=["Report"])
api_router.include_router(history_router, prefix="/history", tags=["History"])

# ─────────────────────────────────────────────
# Admin Routes
# ─────────────────────────────────────────────

api_router.include_router(
    admin_router,
    prefix="/admin",
    tags=["Admin"],
)

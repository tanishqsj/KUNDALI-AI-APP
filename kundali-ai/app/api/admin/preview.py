from fastapi import APIRouter, Depends

from app.api.dependencies import require_admin
from app.api.admin.rules import router as rules_router
from app.api.admin.preview_routes import router as preview_routes_router


router = APIRouter(
    dependencies=[Depends(require_admin)]
)

router.include_router(
    rules_router,
    prefix="/rules",
    tags=["Admin – Rules"],
)

router.include_router(
    preview_routes_router,
    prefix="/preview",
    tags=["Admin – Preview"],
)

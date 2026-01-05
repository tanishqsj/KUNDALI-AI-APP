from fastapi import APIRouter, Depends

from app.api.dependencies import require_admin
from app.api.admin.rules import router as rules_router
from app.api.admin.preview import router as preview_router
from app.api.admin.usage import router as usage_router


router = APIRouter(
    dependencies=[Depends(require_admin)]
)

router.include_router(
    rules_router,
    prefix="/rules",
    tags=["Admin – Rules"],
)

router.include_router(
    preview_router,
    prefix="/preview",
    tags=["Admin – Preview"],
)

router.include_router(
    usage_router,
    prefix="/usage",
    tags=["Admin – Usage"],
)

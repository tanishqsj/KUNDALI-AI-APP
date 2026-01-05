from fastapi import APIRouter, Depends
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.persistence.db import get_db_session
from app.services.usage_service import UsageService


router = APIRouter()


@router.get(
    "/usage/user/{user_id}",
    summary="Get usage summary for a user",
)
async def get_user_usage(
    user_id: UUID,
    start: datetime | None = None,
    end: datetime | None = None,
    session: AsyncSession = Depends(get_db_session),
    admin=Depends(require_admin),
):
    """
    Inspect usage logs for a specific user.
    """
    service = UsageService()
    return await service.get_user_usage(
        session=session,
        user_id=user_id,
        start=start,
        end=end,
    )


@router.get(
    "/usage/feature/{feature}",
    summary="Get usage summary for a feature",
)
async def get_feature_usage(
    feature: str,
    start: datetime | None = None,
    end: datetime | None = None,
    session: AsyncSession = Depends(get_db_session),
    admin=Depends(require_admin),
):
    """
    Inspect usage logs for a feature across all users.
    """
    service = UsageService()
    return await service.get_feature_usage(
        session=session,
        feature=feature,
        start=start,
        end=end,
    )

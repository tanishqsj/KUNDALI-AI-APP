from fastapi import Depends, HTTPException, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.db import get_db_session
from app.persistence.repositories.user_repo import UserRepository


class CurrentUser:
    """
    Lightweight user context injected into APIs.
    """

    def __init__(self, id: UUID, is_admin: bool):
        self.id = id
        self.is_admin = is_admin


async def get_current_user(
    session: AsyncSession = Depends(get_db_session),
) -> CurrentUser:
    """
    Resolve currently authenticated user.

    NOTE:
    This is a placeholder implementation.
    Replace with JWT / OAuth / session logic later.
    """

    # TEMP: hardcoded user (for dev & Insomnia testing)
    user_id = UUID("00000000-0000-0000-0000-000000000001")

    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    return CurrentUser(
        id=user.id,
        is_admin=user.is_admin,
    )


async def require_admin(
    user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    Ensure the current user is an admin.
    """

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return user

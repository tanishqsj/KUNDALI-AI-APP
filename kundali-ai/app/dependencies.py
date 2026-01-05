from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.persistence.db import get_db_session


async def get_db(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncSession:
    """
    Global DB dependency.

    This simply re-exports the main DB session dependency
    for convenience across the app.
    """
    return session

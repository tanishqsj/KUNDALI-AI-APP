from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.repositories.base import BaseRepository
from app.persistence.models.user import User


class UserRepository(BaseRepository[User]):
    """
    Repository for User model.
    """

    model = User

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_email(self, email: str) -> User | None:
        """
        Fetch a user by email.
        """
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_admins(self) -> list[User]:
        """
        Fetch all admin users.
        """
        stmt = select(User).where(User.is_admin.is_(True))
        result = await self.session.execute(stmt)
        return result.scalars().all()

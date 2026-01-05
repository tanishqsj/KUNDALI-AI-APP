from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.repositories.base import BaseRepository
from app.persistence.models.birth_profile import BirthProfile


class BirthProfileRepository(BaseRepository[BirthProfile]):
    """
    Repository for BirthProfile model.

    Birth profiles are treated as immutable input data.
    """

    model = BirthProfile

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    # ─────────────────────────────────────────────
    # Create
    # ─────────────────────────────────────────────

    async def create(
        self,
        *,
        user_id,
        name: str,
        birth_date,
        birth_time,
        birth_place: str,
        latitude: float,
        longitude: float,
        timezone: str,
    ) -> BirthProfile:
        """
        Create a new immutable birth profile.
        """

        profile = BirthProfile(
            user_id=user_id,
            name=name,
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_place,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
        )

        self.session.add(profile)

        # Flush to assign PK without committing
        await self.session.flush()

        return profile

    # ─────────────────────────────────────────────
    # Queries
    # ─────────────────────────────────────────────

    async def list_by_user(
        self,
        user_id,
        limit: int = 50,
        offset: int = 0
    ) -> list[BirthProfile]:
        """
        Fetch birth profiles belonging to a specific user.
        """
        stmt = (
            select(BirthProfile)
            .where(BirthProfile.user_id == user_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_exact_birth_data(
        self,
        birth_date,
        birth_time,
        birth_place: str,
        latitude,
        longitude,
        timezone,
    ) -> BirthProfile | None:
        """
        Fetch a birth profile matching exact birth inputs.

        Used to prevent accidental duplication.
        """
        stmt = select(BirthProfile).where(
            BirthProfile.birth_date == birth_date,
            BirthProfile.birth_time == birth_time,
            BirthProfile.birth_place == birth_place,
            BirthProfile.latitude == latitude,
            BirthProfile.longitude == longitude,
            BirthProfile.timezone == timezone,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

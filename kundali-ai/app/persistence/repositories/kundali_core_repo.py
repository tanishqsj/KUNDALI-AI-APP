from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.repositories.base import BaseRepository
from app.persistence.models.kundali_core import KundaliCore


class KundaliCoreRepository(BaseRepository[KundaliCore]):
    """
    Repository for KundaliCore model.

    KundaliCore represents immutable astronomical truth (D1 chart).
    """

    model = KundaliCore

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create(
        self,
        *,
        birth_profile_id,
        ascendant,
        planets,
        houses,
        ayanamsa,
    ) -> KundaliCore:
        kundali_core = KundaliCore(
            birth_profile_id=birth_profile_id,
            ascendant=ascendant,
            planets=planets,
            houses=houses,
            ayanamsa=ayanamsa,
        )

        self.session.add(kundali_core)
        await self.session.flush()  # IMPORTANT: generates ID

        return kundali_core

    async def get_by_birth_profile(
        self,
        birth_profile_id
    ) -> KundaliCore | None:
        """
        Fetch the kundali core for a given birth profile.

        There can be only ONE kundali core per birth profile.
        """
        stmt = select(KundaliCore).where(
            KundaliCore.birth_profile_id == birth_profile_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_for_birth_profile(
        self,
        birth_profile_id
    ) -> bool:
        """
        Check if a kundali core already exists for a birth profile.
        """
        stmt = select(KundaliCore.id).where(
            KundaliCore.birth_profile_id == birth_profile_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

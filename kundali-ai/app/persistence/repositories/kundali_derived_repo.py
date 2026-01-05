from uuid import UUID
from sqlalchemy import select

from app.persistence.models.kundali_derived import KundaliDerived
from app.persistence.repositories.base import BaseRepository


class KundaliDerivedRepository(BaseRepository):
    """
    Repository for KundaliDerived persistence.
    """

    async def create(
        self,
        *,
        kundali_core_id: UUID,
        doshas,
        yogas,
        planet_strengths,
        house_strengths,
        summary,
        calculation_version: str,
    ) -> KundaliDerived:
        obj = KundaliDerived(
            kundali_core_id=kundali_core_id,
            doshas=doshas,
            yogas=yogas,
            planet_strengths=planet_strengths,
            house_strengths=house_strengths,
            summary=summary,
            calculation_version=calculation_version,
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_by_core_id(
        self,
        kundali_core_id: UUID,
    ) -> KundaliDerived:
        stmt = select(KundaliDerived).where(KundaliDerived.kundali_core_id == kundali_core_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

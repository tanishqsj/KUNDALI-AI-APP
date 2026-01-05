from uuid import UUID
from sqlalchemy import select

from app.persistence.models.kundali_divisional import KundaliDivisional
from app.persistence.repositories.base import BaseRepository


class KundaliDivisionalRepository(BaseRepository[KundaliDivisional]):
    """
    Repository for KundaliDivisional persistence.
    One row per divisional chart (D9, D10, etc.)
    """

    async def create_many(
        self,
        *,
        kundali_core_id: UUID,
        charts: dict,
        calculation_version: str,
    ) -> list[KundaliDivisional]:

        objects: list[KundaliDivisional] = []

        for chart_type, chart_data in charts.items():
            obj = KundaliDivisional(
                kundali_core_id=kundali_core_id,
                chart_type=chart_type,
                chart_data=chart_data,
                calculation_version=calculation_version,
            )
            self.session.add(obj)
            objects.append(obj)

        await self.session.flush()
        return objects

    async def get_by_core_id(
        self,
        kundali_core_id: UUID,
    ) -> list[KundaliDivisional]:
        stmt = select(KundaliDivisional).where(KundaliDivisional.kundali_core_id == kundali_core_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

from datetime import date, time
from typing import Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.kundali_cache import KundaliCache
from app.domain.kundali.engine import KundaliEngine, BirthInput
from app.domain.kundali.calculator import KundaliCalculator
from app.domain.kundali.converters import kundali_core_to_persistence
from app.domain.kundali.derived.derived_builder import DerivedBuilder
from app.domain.kundali.divisional.divisional_builder import DivisionalBuilder

from app.persistence.repositories.birth_profile_repo import BirthProfileRepository
from app.persistence.repositories.kundali_core_repo import KundaliCoreRepository
from app.persistence.repositories.kundali_derived_repo import KundaliDerivedRepository
from app.persistence.repositories.kundali_divisional_repo import KundaliDivisionalRepository


class KundaliService:
    """
    Core orchestration service for kundali generation.
    """

    def __init__(self):
        self.calculator = KundaliCalculator()
        self.engine = KundaliEngine(self.calculator)
        self.derived_builder = DerivedBuilder()
        self.divisional_builder = DivisionalBuilder()
        self.cache = KundaliCache()

    async def create_kundali(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:

        cached = await self.cache.get_kundali(
            user_id=user_id,
            kundali_core_id=payload.get("kundali_core_id"),
        )
        if cached:
            return cached

        birth_repo = BirthProfileRepository(session)
        core_repo = KundaliCoreRepository(session)
        derived_repo = KundaliDerivedRepository(session)
        divisional_repo = KundaliDivisionalRepository(session)

        birth_date=date.fromisoformat(payload["birth_date"])
        birth_time=time.fromisoformat(payload["birth_time"])

        # 1. Birth profile
        birth_profile = await birth_repo.create(
            user_id=user_id,
            name=payload["name"],
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=payload["birth_place"],
            latitude=payload["latitude"],
            longitude=payload["longitude"],
            timezone=payload["timezone"],
        )

        # 2. Kundali (D1)
        birth_input = BirthInput(
            birth_date=birth_date,
            birth_time=birth_time,
            latitude=payload["latitude"],
            longitude=payload["longitude"],
            timezone=payload["timezone"],
        )

        kundali_chart = self.engine.generate(birth_input)
        core_json = kundali_core_to_persistence(kundali_chart)

        kundali_core = await core_repo.create(
            birth_profile_id=birth_profile.id,
            ascendant=core_json["ascendant"],
            planets=core_json["planets"],
            houses=core_json["houses"],
            ayanamsa=kundali_chart.ayanamsa,
        )

        # 3. Derived
        derived = self.derived_builder.build(kundali_chart)

        await derived_repo.create(
            kundali_core_id=kundali_core.id,
            doshas=[d.model_dump() for d in derived.doshas],
            yogas=[y.model_dump() for y in derived.yogas],
            planet_strengths={k: v.model_dump() for k, v in derived.planet_strengths.items()},
            house_strengths={k: v.model_dump() for k, v in derived.house_strengths.items()},
            summary=derived.summary,
            calculation_version=derived.calculation_version,
        )

        # 4. Divisional
        divisional = self.divisional_builder.build(kundali_chart)

        await divisional_repo.create_many(
        kundali_core_id=kundali_core.id,
        charts={
            k: v.model_dump()
            for k, v in divisional.charts.items()
        },
        calculation_version=divisional.calculation_version,
        )


        await session.commit()

        result = {
            "birth_profile_id": birth_profile.id,
            "kundali_core_id": kundali_core.id,
            "kundali": kundali_chart.model_dump(),
            "derived": derived.model_dump(),
            "divisional": divisional.model_dump(),
        }

        await self.cache.set_kundali(
            user_id=user_id,
            kundali_core_id=kundali_core.id,
            data=result,
        )

        return result

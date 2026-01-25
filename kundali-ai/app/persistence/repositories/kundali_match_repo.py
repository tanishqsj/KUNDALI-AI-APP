"""
Repository for Kundali Match operations.
"""

from uuid import UUID
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.persistence.models.kundali_match import KundaliMatch


class KundaliMatchRepository:
    """Repository for Kundali Match CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: UUID,
        boy_kundali_id: UUID,
        girl_kundali_id: UUID,
        total_score: float,
        max_score: int,
        verdict: str,
        factors: dict,
    ) -> KundaliMatch:
        """Create a new matching record."""
        match = KundaliMatch(
            user_id=user_id,
            boy_kundali_id=boy_kundali_id,
            girl_kundali_id=girl_kundali_id,
            total_score=total_score,
            max_score=max_score,
            verdict=verdict,
            factors=factors,
        )
        self.session.add(match)
        await self.session.commit()
        await self.session.refresh(match)
        return match

    async def get_by_id(self, match_id: UUID) -> Optional[KundaliMatch]:
        """Get a match by ID."""
        result = await self.session.execute(
            select(KundaliMatch).where(KundaliMatch.id == match_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: UUID) -> List[KundaliMatch]:
        """Get all matches for a user."""
        result = await self.session.execute(
            select(KundaliMatch)
            .where(KundaliMatch.user_id == user_id)
            .order_by(KundaliMatch.created_at.desc())
        )
        return result.scalars().all()

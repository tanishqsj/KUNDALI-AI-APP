# Placeholder for kundali-ai/app/persistence/repositories/base.py
from typing import Generic, TypeVar, Type, Sequence, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.persistence.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic async repository for CRUD operations.

    Concrete repositories should extend this class
    and provide the model via the `model` attribute.
    """

    model: Type[ModelType]

    def __init__(self, session: AsyncSession):
        self.session = session

    # ─────────────────────────────────────────────
    # Create
    # ─────────────────────────────────────────────

    async def add(self, instance: ModelType) -> ModelType:
        self.session.add(instance)
        await self.session.flush()
        return instance

    # ─────────────────────────────────────────────
    # Read
    # ─────────────────────────────────────────────

    async def get_by_id(self, id) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Sequence[ModelType]:
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # ─────────────────────────────────────────────
    # Delete
    # ─────────────────────────────────────────────

    async def delete(self, instance: ModelType) -> None:
        await self.session.delete(instance)

    # ─────────────────────────────────────────────
    # Persistence
    # ─────────────────────────────────────────────

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

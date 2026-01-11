from typing import List, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# We don't need to import Vector here, just use the model field methods

from app.persistence.repositories.base import BaseRepository
from app.persistence.models.knowledge_item import KnowledgeItem


class KnowledgeRepository(BaseRepository[KnowledgeItem]):
    """
    Repository for RAG knowledge base items.
    Handles vector similarity search.
    """

    model = KnowledgeItem

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def search_similar(
        self, 
        embedding_vector: List[float], 
        limit: int = 3
    ) -> Sequence[KnowledgeItem]:
        """
        Find items semantically similar to the query vector
        using L2 distance (Euclidean distance).
        """
        stmt = select(self.model).order_by(
            self.model.embedding.l2_distance(embedding_vector)
        ).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()
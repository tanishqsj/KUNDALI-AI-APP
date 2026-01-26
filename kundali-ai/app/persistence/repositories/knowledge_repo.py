from typing import List, Sequence, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# We don't need to import Vector here, just use the model field methods

from app.persistence.repositories.base import BaseRepository
from app.persistence.models.knowledge_item import KnowledgeItem


class KnowledgeRepository(BaseRepository[KnowledgeItem]):
    """
    Repository for RAG knowledge base items.
    Handles vector similarity search with quality scoring.
    """

    model = KnowledgeItem

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def search_similar(
        self, 
        embedding_vector: List[float], 
        limit: int = 5
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

    async def search_with_distances(
        self, 
        embedding_vector: List[float], 
        limit: int = 10,
        filter_category: str | None = None,
        filter_keywords: List[str] | None = None,
    ) -> List[Tuple[KnowledgeItem, float]]:
        """
        Find items with their L2 distance scores, optionally filtered by metadata.
        """
        distance_expr = self.model.embedding.l2_distance(embedding_vector)
        
        stmt = select(
            self.model,
            distance_expr.label('distance')
        )

        # Apply filters
        if filter_category:
            stmt = stmt.where(self.model.category == filter_category)
            
        if filter_keywords:
            # Basic keyword match (OR logic)
            # This checks if any keyword is present in the keywords string
            for kw in filter_keywords:
                stmt = stmt.where(self.model.keywords.ilike(f"%{kw}%"))

        stmt = stmt.order_by(distance_expr).limit(limit)

        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.fetchall()]

    async def search_with_threshold(
        self, 
        embedding_vector: List[float], 
        threshold: float = 1.2,
        limit: int = 10
    ) -> List[Tuple[KnowledgeItem, float]]:
        """
        Search with a distance threshold to filter irrelevant results.
        Only returns items with distance < threshold.
        """
        distance_expr = self.model.embedding.l2_distance(embedding_vector)
        
        stmt = select(
            self.model,
            distance_expr.label('distance')
        ).where(
            distance_expr < threshold
        ).order_by(distance_expr).limit(limit)

        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.fetchall()]
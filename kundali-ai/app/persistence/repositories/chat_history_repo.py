from uuid import UUID
from typing import List, Sequence
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.models.chat_history import ChatHistory

class ChatHistoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_message(
        self,
        *,
        user_id: UUID,
        role: str,
        content: str,
        kundali_core_id: UUID | None = None
    ) -> ChatHistory:
        """
        Add a new message to the history.
        """
        msg = ChatHistory(
            user_id=user_id,
            role=role,
            content=content,
            kundali_core_id=kundali_core_id
        )
        self.session.add(msg)
        await self.session.commit()
        await self.session.refresh(msg)
        return msg

    async def get_history(
        self,
        user_id: UUID,
        kundali_core_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> Sequence[ChatHistory]:
        """
        Get chat history for a user (and optionally a specific kundali),
        ordered by time ascending (oldest first).
        """
        stmt = (
            select(ChatHistory)
            .where(ChatHistory.user_id == user_id)
        )

        if kundali_core_id:
             stmt = stmt.where(ChatHistory.kundali_core_id == kundali_core_id)

        stmt = (
            stmt.order_by(ChatHistory.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

from typing import List, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.db import get_db_session
from app.persistence.repositories.chat_history_repo import ChatHistoryRepository

router = APIRouter()

@router.get("/{kundali_id}", response_model=List[Any])
async def get_chat_history(
    kundali_id: UUID,
    user_id: UUID, # Passed as query param for now, should be from Auth but Auth is loose here
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get chat history for a specific user. 
    Note: We filter by user_id primarily as that's the main owner.
    """
    repo = ChatHistoryRepository(session)
    history = await repo.get_history(user_id, kundali_core_id=kundali_id, limit=limit)
    
    # Format for frontend
    return [
        {
            "role": msg.role,
            "text": msg.content,
            "timestamp": msg.created_at.isoformat() if msg.created_at else None
        }
        for msg in history
    ]

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.schemas.conversation import ConversationCreate, ConversationUpdate
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation, ConversationCreate, ConversationUpdate]):
    """Repository for conversation operations."""

    def __init__(self):
        super().__init__(Conversation)
    
    async def get_by_user_session_id(
        self, db: AsyncSession, *, user_session_id: str, skip: int = 0, limit: int = 100
    ) -> List[Conversation]:
        """Get conversations by user session ID."""
        query = select(self.model).where(
            self.model.user_session_id == user_session_id
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_active_by_user_session_id(
        self, db: AsyncSession, *, user_session_id: str
    ) -> Optional[Conversation]:
        """Get active conversation by user session ID."""
        query = select(self.model).where(
            self.model.user_session_id == user_session_id,
            self.model.is_active == True
        ).order_by(self.model.created_at.desc())
        result = await db.execute(query)
        return result.scalars().first()
    
    async def deactivate_conversation(self, db: AsyncSession, *, id: str) -> Optional[Conversation]:
        """Deactivate a conversation."""
        conversation = await self.get(db=db, id=id)
        if conversation:
            conversation.is_active = False
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
        return conversation 
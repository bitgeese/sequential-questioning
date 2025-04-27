from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.schemas.message import MessageCreate, MessageUpdate
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message, MessageCreate, MessageUpdate]):
    """Repository for message operations."""

    def __init__(self):
        super().__init__(Message)
    
    async def get_by_conversation_id(
        self, db: AsyncSession, *, conversation_id: str, skip: int = 0, limit: int = 100
    ) -> List[Message]:
        """Get messages by conversation ID, ordered by sequence number."""
        query = select(self.model).where(
            self.model.conversation_id == conversation_id
        ).order_by(self.model.sequence_number).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_conversation_id_and_type(
        self, db: AsyncSession, *, conversation_id: str, message_type: str, skip: int = 0, limit: int = 100
    ) -> List[Message]:
        """Get messages by conversation ID and message type."""
        query = select(self.model).where(
            self.model.conversation_id == conversation_id,
            self.model.message_type == message_type
        ).order_by(self.model.sequence_number).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_latest_message(self, db: AsyncSession, *, conversation_id: str) -> Optional[Message]:
        """Get the latest message in a conversation."""
        query = select(self.model).where(
            self.model.conversation_id == conversation_id
        ).order_by(self.model.sequence_number.desc())
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_next_sequence_number(self, db: AsyncSession, *, conversation_id: str) -> int:
        """Get the next sequence number for a message in a conversation."""
        latest_message = await self.get_latest_message(db=db, conversation_id=conversation_id)
        if latest_message:
            return latest_message.sequence_number + 1
        return 1
        
    async def count_by_conversation(
        self, db: AsyncSession, *, conversation_id: str, message_type: Optional[str] = None
    ) -> int:
        """Count messages in a conversation, optionally filtering by type."""
        query = select(func.count()).select_from(self.model).where(
            self.model.conversation_id == conversation_id
        )
        
        if message_type:
            query = query.where(self.model.message_type == message_type)
            
        result = await db.execute(query)
        return result.scalar_one() or 0 
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_session import UserSession
from app.schemas.user_session import UserSessionCreate, UserSessionUpdate
from app.repositories.base import BaseRepository


class UserSessionRepository(BaseRepository[UserSession, UserSessionCreate, UserSessionUpdate]):
    """Repository for user session operations."""

    def __init__(self):
        super().__init__(UserSession)
    
    async def get_by_user_identifier(self, db: AsyncSession, *, user_identifier: str) -> Optional[UserSession]:
        """Get a user session by user identifier."""
        query = select(self.model).where(self.model.user_identifier == user_identifier)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_active_sessions(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[UserSession]:
        """Get all active user sessions."""
        query = select(self.model).where(self.model.is_active == True).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def deactivate_session(self, db: AsyncSession, *, id: str) -> Optional[UserSession]:
        """Deactivate a user session."""
        session = await self.get(db=db, id=id)
        if session:
            session.is_active = False
            db.add(session)
            await db.commit()
            await db.refresh(session)
        return session 
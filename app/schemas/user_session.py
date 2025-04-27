from pydantic import BaseModel, Field
from typing import Optional, List, ClassVar, Type
from datetime import datetime
from uuid import uuid4
from app.schemas.conversation import ConversationResponse


class UserSessionBase(BaseModel):
    """Base schema for user session with common attributes."""
    user_identifier: Optional[str] = None
    context: Optional[str] = None
    is_active: bool = True


class UserSessionCreate(UserSessionBase):
    """Schema for creating a new user session."""
    pass


class UserSessionUpdate(UserSessionBase):
    """Schema for updating an existing user session."""
    user_identifier: Optional[str] = None
    context: Optional[str] = None
    is_active: Optional[bool] = None


class UserSessionInDB(UserSessionBase):
    """Schema for user session data as stored in the database."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserSessionResponse(UserSessionInDB):
    """Schema for user session data returned in API responses."""
    pass


class UserSessionWithConversations(UserSessionResponse):
    """Schema for user session with related conversations."""
    conversations: List[ConversationResponse] = [] 
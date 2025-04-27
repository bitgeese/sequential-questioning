from pydantic import BaseModel, Field
from typing import Optional, List, ClassVar, Type
from datetime import datetime
from uuid import uuid4
from app.schemas.message import MessageResponse


class ConversationBase(BaseModel):
    """Base schema for conversation with common attributes."""
    topic: Optional[str] = None
    is_active: bool = True


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""
    user_session_id: str


class ConversationUpdate(ConversationBase):
    """Schema for updating an existing conversation."""
    topic: Optional[str] = None
    is_active: Optional[bool] = None


class ConversationInDB(ConversationBase):
    """Schema for conversation data as stored in the database."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_session_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(ConversationInDB):
    """Schema for conversation data returned in API responses."""
    pass


class ConversationWithMessages(ConversationResponse):
    """Schema for conversation with related messages."""
    messages: List[MessageResponse] = []
    MessageResponse: ClassVar[Type] = MessageResponse 
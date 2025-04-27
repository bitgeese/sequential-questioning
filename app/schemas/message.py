from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
import json


class MessageBase(BaseModel):
    """Base schema for message with common attributes."""
    message_type: str  # 'question', 'answer', 'system'
    content: str
    message_metadata: Optional[Dict[str, Any]] = None
    sequence_number: int


class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    conversation_id: str

    class Config:
        json_encoders = {
            dict: lambda v: json.dumps(v)
        }


class MessageUpdate(BaseModel):
    """Schema for updating an existing message."""
    message_type: Optional[str] = None
    content: Optional[str] = None
    message_metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            dict: lambda v: json.dumps(v)
        }


class MessageInDB(MessageBase):
    """Schema for message data as stored in the database."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @property
    def metadata_dict(self) -> Dict[str, Any]:
        """Parse the metadata JSON string into a dictionary."""
        if not self.message_metadata:
            return {}
        if isinstance(self.message_metadata, dict):
            return self.message_metadata
        try:
            return json.loads(self.message_metadata)
        except (json.JSONDecodeError, TypeError):
            return {}


class MessageResponse(MessageInDB):
    """Schema for message data returned in API responses."""
    pass 
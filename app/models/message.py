from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
import enum

from app.models.database import Base


class MessageType(str, enum.Enum):
    """Enum representing the types of messages in a conversation."""
    QUESTION = "question"
    ANSWER = "answer"
    SYSTEM = "system"


class Message(Base):
    """Model representing a message in a conversation.
    
    A message can be a question or an answer within a conversation.
    """
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    message_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column(Text, nullable=True)  # JSON string for additional metadata
    sequence_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, type={self.message_type})>" 
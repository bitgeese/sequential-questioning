from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4


class MessageItem(BaseModel):
    """Schema for a message item within the question generation context."""
    role: str = Field(
        ..., 
        description="Role of the message sender",
        examples=["user", "assistant", "system"]
    )  # 'user', 'assistant', 'system'
    content: str = Field(
        ..., 
        description="Content of the message"
    )
    timestamp: Optional[datetime] = Field(
        None,
        description="Optional timestamp of when the message was sent",
        json_schema_override={"type": ["string", "null"], "format": "date-time"}
    )


class QuestionItem(BaseModel):
    """Schema for a single question within a sequence."""
    question_text: str = Field(..., description="The generated question text")
    question_number: int = Field(..., description="Position of this question in the sequence")
    metadata: Optional[Dict[str, str]] = Field(
        None,
        description="Additional metadata specific to this question",
        examples=[{
            "importance": "This question helps understand user goals",
            "information_to_look_for": "Specific details about timing and priorities"
        }],
        json_schema_override={"type": ["object", "null"]}
    )


class QuestionRequest(BaseModel):
    """Schema for question generation request."""
    user_id: Optional[str] = Field(
        None,
        description="Optional user identifier",
        json_schema_override={"type": ["string", "null"]}
    )
    conversation_id: Optional[str] = Field(
        None,
        description="Conversation identifier for maintaining context continuity; if omitted a new conversation will be created",
        json_schema_override={"type": ["string", "null"]}
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session identifier",
        json_schema_override={"type": ["string", "null"]}
    )
    context: Optional[str] = Field(
        None,
        description="Optional context information for the question generation",
        json_schema_override={"type": ["string", "null"]}
    )
    previous_messages: Optional[List[MessageItem]] = Field(
        None,
        description="Optional list of previous messages in the conversation",
        json_schema_override={"type": ["array", "null"]}
    )
    metadata: Optional[Dict[str, str]] = Field(
        None,
        description="Optional metadata for the request. Values should be strings.",
        examples=[{"source": "chat_interface", "version": "1.0"}],
        json_schema_override={"type": ["object", "null"]}
    )
    

class QuestionResponse(BaseModel):
    """Schema for question generation response."""
    current_question: str = Field(..., description="The current question to show to the user")
    questions: List[QuestionItem] = Field(..., description="List of generated questions in this batch")
    conversation_id: str = Field(..., description="The conversation identifier")
    session_id: str = Field(..., description="The session identifier")
    current_question_number: int = Field(1, description="Current question number to display")
    total_questions_in_batch: int = Field(..., description="Total questions generated in this batch")
    total_questions_estimated: int = Field(5, description="Estimated total questions for the entire conversation")
    next_batch_needed: bool = Field(True, description="Whether another batch of questions will be needed after this one")
    metadata: Optional[Dict[str, str]] = Field(
        None,
        description="Optional metadata for the response",
        examples=[{
            "question_type": "follow_up",
            "context_enhanced": "true",
            "timestamp": "2023-09-28T15:30:45.123456"
        }],
        json_schema_override={"type": ["object", "null"]}
    )
    
    # Removed model_config overrides; using json_schema_override for optional field types 
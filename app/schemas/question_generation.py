from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4


class MessageItem(BaseModel):
    """Schema for a message item within the question generation context."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: Optional[datetime] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "role": "user",
                    "content": "Hello, I need help with planning.",
                    "timestamp": "2025-04-26T23:00:00"
                }
            ]
        }
    }


class QuestionItem(BaseModel):
    """Schema for a single question within a sequence."""
    question_text: str = Field(..., description="The generated question text")
    question_number: int = Field(..., description="Position of this question in the sequence")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata specific to this question")


class QuestionRequest(BaseModel):
    """Schema for question generation request."""
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    conversation_id: Optional[str] = Field(None, description="Optional conversation identifier")
    session_id: Optional[str] = Field(None, description="Optional session identifier")
    context: Optional[str] = Field(None, description="Optional context information for the question generation")
    previous_messages: Optional[List[MessageItem]] = Field(None, description="Optional list of previous messages in the conversation")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata for the request")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "context": "User has requested help creating a plan for next month.",
                    "previous_messages": [
                        {
                            "role": "user", 
                            "content": "I need help planning my schedule.",
                            "timestamp": "2025-04-26T23:00:00"
                        }
                    ]
                }
            ]
        }
    }


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
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata for the response")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "current_question": "What specific goals would you like to achieve next month?",
                    "questions": [
                        {"question_text": "What specific goals would you like to achieve next month?", "question_number": 1},
                        {"question_text": "How much time can you dedicate to these goals weekly?", "question_number": 2},
                        {"question_text": "What resources do you already have available?", "question_number": 3}
                    ],
                    "conversation_id": "abc123",
                    "session_id": "xyz789",
                    "current_question_number": 1,
                    "total_questions_in_batch": 3,
                    "total_questions_estimated": 8,
                    "next_batch_needed": True
                }
            ]
        }
    } 
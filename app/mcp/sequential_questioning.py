from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import time
from datetime import datetime

from app.core.logging import app_logger
from app.core.monitoring import log_request
from app.models.database import get_db
from app.services.question_generation import question_generation_service
from app.schemas.question_generation import QuestionRequest, QuestionResponse, MessageItem

# Create router for sequential questioning MCP
router = APIRouter()

class EnhancedQuestionRequest(QuestionRequest):
    """Enhanced question request that supports automatic follow-up handling."""
    auto_follow_up: Optional[bool] = Field(
        False, 
        description="Flag to indicate if follow-up questions should be generated automatically"
    )
    # Merge base class nullable properties with subclass nullable field
    model_config = {
        "json_schema_extra": {
            "properties": {
                **QuestionRequest.model_config.get("json_schema_extra", {}).get("properties", {}),
                "auto_follow_up": {"nullable": True}
            }
        }
    }

class AutomaticQuestioningRequest(QuestionRequest):
    """Request schema for automatic questioning that handles follow-ups within a single call."""
    auto_handle_follow_up: bool = Field(
        True, 
        description="Flag to enable automatic follow-up question generation"
    )
    max_rounds: Optional[int] = Field(
        2,  
        description="Maximum number of question rounds to handle automatically (capped at 3)",
        ge=1,
        le=3
    )
    # Merge base class nullable properties with subclass nullable field
    model_config = {
        "json_schema_extra": {
            "properties": {
                **QuestionRequest.model_config.get("json_schema_extra", {}).get("properties", {}),
                "max_rounds": {"nullable": True}
            }
        }
    }

class AutomaticQuestioningResponse(BaseModel):
    """Response schema for automatic questioning that includes all question rounds."""
    initial_questions: QuestionResponse = Field(
        ..., 
        description="Initial set of questions generated in the first round"
    )
    follow_up_questions: Optional[List[QuestionResponse]] = Field(
        None, 
        description="Optional list of follow-up question responses for subsequent rounds"
    )
    all_questions_combined: str = Field(
        ..., 
        description="All questions from all rounds combined into a single string in numbered list format"
    )
    conversation_id: str = Field(
        ..., 
        description="The conversation identifier for this questioning session"
    )
    session_id: str = Field(
        ..., 
        description="The session identifier for this questioning session"
    )
    total_questions: int = Field(
        ..., 
        description="Total number of questions generated across all rounds"
    )
    metadata: Optional[Dict[str, str]] = Field(
        None, 
        description="Optional metadata containing additional information about the questioning process",
        examples=[{
            "rounds_generated": "3",
            "timestamp": "2023-09-28T15:30:45.123456",
            "auto_follow_up": "true"
        }]
    )

    model_config = {
        "json_schema_extra": {
            "properties": {
                "follow_up_questions": {"nullable": True}, # Explicitly mark optional fields as nullable
                "metadata": {"nullable": True}
            }
        }
    }

@router.post(
    "/question", 
    response_model=QuestionResponse,
    operation_id="sequential_questioning",
    summary="Generate a batch of sequential questions based on conversation context",
    description="This MCP endpoint generates multiple contextual, sequential questions based on conversation history and context, presented in a numbered list format. Returns a conversation_id that should be passed in follow-up requests for conversation continuity.",
    tags=["mcp"]
)
@log_request(endpoint="sequential_questioning", log_inputs=True)
async def generate_sequential_question(
    request: EnhancedQuestionRequest,
    db: AsyncSession = Depends(get_db)
):
    """MCP endpoint for sequential questioning.
    
    This endpoint is designed to be called by LLMs or other MCP clients
    and generates multiple contextual, sequential questions based on previous
    interactions. The questions are presented in a numbered list format.
    
    The endpoint processes the conversation history and context provided
    and generates the next logical set of questions to ask. It maintains context
    across multiple calls by storing conversation state in the database.
    
    Args:
        request: The question generation request containing context and previous messages
        db: Database session dependency
    
    Returns:
        A response containing generated questions in numbered format and metadata
    """
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            app_logger.info(f"Processing sequential questioning request with context length: {len(request.context or '')}")
            
            # Generate the next question using the question generation service
            response = await question_generation_service.generate_question(db, request)
            
            # Format the response to display all questions at once in a numbered list
            formatted_questions = "\n".join([
                f"{q.question_number}. {q.question_text}" 
                for q in sorted(response.questions, key=lambda x: x.question_number)
            ])
            
            # Update the response with the formatted questions
            response.current_question = formatted_questions
            
            # Log the conversation ID
            app_logger.info(f"Generated questions for conversation ID: {response.conversation_id}")
            
            return response
            
        except Exception as e:
            retry_count += 1
            app_logger.exception(f"Error in sequential questioning endpoint (attempt {retry_count}/{max_retries}): {str(e)}")
            
            if "Received request before initialization was complete" in str(e):
                # This is a timing issue with the MCP connection, retry after a delay
                app_logger.warning(f"MCP initialization timing issue detected, retrying after delay...")
                await asyncio.sleep(1)  # Add a 1-second delay before retrying
                continue
                
            if retry_count >= max_retries:
                # If we've exhausted our retries, raise the exception
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate question after {max_retries} attempts: {str(e)}"
                )
            
            # Add exponential backoff for other errors
            await asyncio.sleep(0.5 * (2 ** (retry_count - 1)))  # 0.5s, 1s, 2s, etc.

@router.post(
    "/question/follow-up", 
    response_model=QuestionResponse,
    operation_id="sequential_questioning_follow_up",
    summary="Generate follow-up questions based on user's answers to previous questions",
    description="This MCP endpoint generates follow-up questions based on the user's answers to previous questions, maintaining the conversation context. While conversation_id is not required, it is STRONGLY RECOMMENDED to provide it for proper conversation continuity. If not provided, a new conversation will be created automatically.",
    tags=["mcp"]
)
@log_request(endpoint="sequential_questioning_follow_up", log_inputs=True)
async def generate_follow_up_questions(
    request: QuestionRequest,
    db: AsyncSession = Depends(get_db)
):
    """MCP endpoint for generating follow-up questions.
    
    This endpoint is specifically designed to generate follow-up questions
    after a user has answered a previous batch of questions. It ensures 
    continuity in the questioning sequence while taking into account
    the user's answers.
    
    Args:
        request: The question request containing previous answers and conversation context
        db: Database session dependency
        
    Returns:
        A response containing the next batch of follow-up questions
        
    Note:
        - conversation_id should be provided whenever possible to maintain conversation continuity
        - If conversation_id is not provided, a new conversation will be created
        - previous_messages are required for this endpoint
    """
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            app_logger.info(f"Processing follow-up questions request with conversation_id: {request.conversation_id}")
            
            # Check if we have previous messages (required for follow-up questions)
            if not request.previous_messages or len(request.previous_messages) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="previous_messages with user answers are required for follow-up questions"
                )
            
            # If no conversation_id is provided, treat it as a new conversation
            if not request.conversation_id:
                app_logger.info("No conversation_id provided for follow-up, creating a new conversation")
                # Create a new request object with the same data
                initial_request = QuestionRequest(
                    user_id=request.user_id,
                    context=request.context or "Follow-up conversation",  # Ensure we have some context
                    previous_messages=[],  # Start fresh for the initial question
                    session_id=request.session_id,
                    metadata=request.metadata
                )
                # Generate initial questions which will create a new conversation
                initial_response = await question_generation_service.generate_question(db, initial_request)
                # Update the request with the new IDs
                request.conversation_id = initial_response.conversation_id
                request.session_id = initial_response.session_id
                
                app_logger.info(f"Created new conversation with ID {request.conversation_id} for follow-up questions")
            
            # Now generate the actual follow-up questions
            response = await question_generation_service.generate_question(db, request)
            
            # Format the response to display all questions at once in a numbered list
            formatted_questions = "\n".join([
                f"{q.question_number}. {q.question_text}" 
                for q in sorted(response.questions, key=lambda x: x.question_number)
            ])
            
            # Update the response with the formatted questions
            response.current_question = formatted_questions
            
            # Log the conversation ID to help troubleshoot
            app_logger.info(f"Returning follow-up questions for conversation ID: {response.conversation_id}")
            
            return response
            
        except HTTPException:
            # Re-raise validation errors without retry
            raise
        except Exception as e:
            retry_count += 1
            app_logger.exception(f"Error in follow-up questions endpoint (attempt {retry_count}/{max_retries}): {str(e)}")
            
            if retry_count >= max_retries:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate follow-up questions after {max_retries} attempts: {str(e)}"
                )
            
            # Add exponential backoff for errors
            await asyncio.sleep(0.5 * (2 ** (retry_count - 1)))

@router.post(
    "/question/automatic",
    response_model=AutomaticQuestioningResponse,
    operation_id="sequential_questioning_automatic",
    summary="Generate questions and automatic follow-ups based on user answers",
    description="This MCP endpoint provides a complete question flow, starting with initial questions and automatically generating follow-up questions based on user responses.",
    tags=["mcp"]
)
@log_request(endpoint="sequential_questioning_automatic", log_inputs=True)
async def automatic_sequential_questioning(
    request: AutomaticQuestioningRequest,
    db: AsyncSession = Depends(get_db)
):
    """MCP endpoint for automatic sequential questioning.
    
    This endpoint handles the complete flow of questioning, including:
    1. Generating initial questions
    2. Automatically generating follow-up questions based on user answers
    3. Combining all questions into a single, cohesive format
    
    Args:
        request: The automatic questioning request
        db: Database session dependency
        
    Returns:
        A response containing all questions from all rounds
    """
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            app_logger.info(f"Processing automatic questioning request with context length: {len(request.context or '')}")
            
            # Generate initial questions
            initial_questions = await question_generation_service.generate_question(db, request)
            
            # Log the conversation ID
            app_logger.info(f"Created/retrieved conversation ID: {initial_questions.conversation_id} for automatic questioning")
            
            # Format initial questions
            initial_formatted = "\n".join([
                f"{q.question_number}. {q.question_text}" 
                for q in sorted(initial_questions.questions, key=lambda x: x.question_number)
            ])
            initial_questions.current_question = initial_formatted
            
            # Initialize follow-up questions list
            follow_up_rounds = []
            all_questions = list(initial_questions.questions)
            
            # If there are previous messages and we need to generate follow-ups
            if (request.previous_messages and 
                len(request.previous_messages) > 0 and 
                initial_questions.next_batch_needed and 
                request.auto_handle_follow_up):
                
                # Maximum number of follow-up rounds
                max_rounds = min(request.max_rounds, 3)  # Cap at 3 to prevent excessive rounds
                current_round = 1
                
                # Use the same conversation and session IDs
                follow_up_request = QuestionRequest(
                    conversation_id=initial_questions.conversation_id,  # Ensure conversation continuity
                    session_id=initial_questions.session_id,
                    context=request.context,
                    previous_messages=request.previous_messages,
                    metadata=request.metadata
                )
                
                app_logger.info(f"Using conversation ID: {follow_up_request.conversation_id} for follow-up rounds")
                
                # Generate follow-up questions for each round
                while current_round < max_rounds and initial_questions.next_batch_needed:
                    # Generate follow-up questions
                    follow_up = await question_generation_service.generate_question(db, follow_up_request)
                    
                    # Format follow-up questions
                    follow_up_formatted = "\n".join([
                        f"{q.question_number}. {q.question_text}" 
                        for q in sorted(follow_up.questions, key=lambda x: x.question_number)
                    ])
                    follow_up.current_question = follow_up_formatted
                    
                    # Add to follow-up rounds and all questions
                    follow_up_rounds.append(follow_up)
                    all_questions.extend(follow_up.questions)
                    
                    # Check if we need more follow-up rounds
                    if not follow_up.next_batch_needed:
                        break
                    
                    current_round += 1
            
            # Combine all questions into one formatted string
            all_questions_combined = "\n".join([
                f"{q.question_number}. {q.question_text}" 
                for q in sorted(all_questions, key=lambda x: x.question_number)
            ])
            
            # Create response with conversation ID clearly included
            response = AutomaticQuestioningResponse(
                initial_questions=initial_questions,
                follow_up_questions=follow_up_rounds if follow_up_rounds else None,
                all_questions_combined=all_questions_combined,  # All questions together in a numbered list
                conversation_id=initial_questions.conversation_id,
                session_id=initial_questions.session_id,
                total_questions=len(all_questions),
                metadata={
                    "rounds_generated": 1 + len(follow_up_rounds),
                    "timestamp": datetime.now().isoformat(),
                    "auto_follow_up": request.auto_handle_follow_up,
                    "conversation_id": initial_questions.conversation_id  # Include in metadata too for clarity
                }
            )
            
            app_logger.info(f"Returning automatic questioning response with conversation ID: {response.conversation_id}")
            
            return response
            
        except Exception as e:
            retry_count += 1
            app_logger.exception(f"Error in automatic questioning endpoint (attempt {retry_count}/{max_retries}): {str(e)}")
            
            if retry_count >= max_retries:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate automatic question flow after {max_retries} attempts: {str(e)}"
                )
            
            # Add exponential backoff for errors
            await asyncio.sleep(0.5 * (2 ** (retry_count - 1))) 
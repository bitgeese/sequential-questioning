from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
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
    auto_follow_up: Optional[bool] = False

class AutomaticQuestioningRequest(QuestionRequest):
    """Request schema for automatic questioning that handles follow-ups within a single call."""
    auto_handle_follow_up: bool = True
    max_rounds: Optional[int] = 2  # Maximum number of question rounds to handle automatically

class AutomaticQuestioningResponse(BaseModel):
    """Response schema for automatic questioning that includes all question rounds."""
    initial_questions: QuestionResponse
    follow_up_questions: Optional[List[QuestionResponse]] = None
    all_questions_combined: str
    conversation_id: str
    session_id: str
    total_questions: int
    metadata: Optional[Dict[str, Any]] = None

@router.post(
    "/question", 
    response_model=QuestionResponse,
    operation_id="sequential_questioning",
    summary="Generate a batch of sequential questions based on conversation context",
    description="This MCP endpoint generates multiple contextual, sequential questions based on conversation history and context, presented in a numbered list format.",
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
            # Replace the single current_question with the full numbered list
            formatted_questions = "\n".join([
                f"{q.question_number}. {q.question_text}" 
                for q in sorted(response.questions, key=lambda x: x.question_number)
            ])
            
            # Update the response with the formatted questions
            response.current_question = formatted_questions
            
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
    description="This MCP endpoint generates follow-up questions based on the user's answers to previous questions, maintaining the conversation context.",
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
    """
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            app_logger.info(f"Processing follow-up questions request for conversation: {request.conversation_id}")
            
            if not request.conversation_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="conversation_id is required for follow-up questions"
                )
                
            if not request.previous_messages or len(request.previous_messages) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="previous_messages with user answers are required for follow-up questions"
                )
            
            # Generate follow-up questions
            response = await question_generation_service.generate_question(db, request)
            
            # Format the response to display all questions at once in a numbered list
            formatted_questions = "\n".join([
                f"{q.question_number}. {q.question_text}" 
                for q in sorted(response.questions, key=lambda x: x.question_number)
            ])
            
            # Update the response with the formatted questions
            response.current_question = formatted_questions
            
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
                    conversation_id=initial_questions.conversation_id,
                    session_id=initial_questions.session_id,
                    context=request.context,
                    previous_messages=request.previous_messages,
                    metadata=request.metadata
                )
                
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
            
            # Create response
            response = AutomaticQuestioningResponse(
                initial_questions=initial_questions,
                follow_up_questions=follow_up_rounds if follow_up_rounds else None,
                all_questions_combined=all_questions_combined,
                conversation_id=initial_questions.conversation_id,
                session_id=initial_questions.session_id,
                total_questions=len(all_questions),
                metadata={
                    "rounds_generated": 1 + len(follow_up_rounds),
                    "timestamp": datetime.now().isoformat(),
                    "auto_follow_up": request.auto_handle_follow_up
                }
            )
            
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
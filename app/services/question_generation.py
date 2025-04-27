from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
from uuid import uuid4
import os
import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import get_settings
from app.core.logging import app_logger
from app.core.monitoring import measure_time
from app.services.vector_db import vector_db_service
from app.repositories.user_session import UserSessionRepository
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.schemas.user_session import UserSessionCreate
from app.schemas.conversation import ConversationCreate
from app.schemas.message import MessageCreate
from app.schemas.question_generation import QuestionRequest, QuestionResponse, MessageItem, QuestionItem
from app.models.message import Message, MessageType
from app.services.vector_search import VectorSearchService
from app.services.service_registry import ServiceRegistry

logger = logging.getLogger(__name__)

settings = get_settings()

# System prompts for question generation
QUESTION_GENERATION_SYSTEM_PROMPT = """
You are an expert question generator for a sequential questioning system.
Your goal is to generate thoughtful, relevant follow-up questions based on previous conversation context.

Guidelines:
1. Generate questions that are clear, specific, and require detailed responses
2. Ensure questions follow logically from previous conversation
3. Avoid questions that have already been answered
4. Focus on gathering missing information relevant to the conversation topic
5. Use information from previous answers to inform new questions

Output should be a single, focused question without any additional commentary or explanation.
"""

INITIAL_QUESTION_GENERATION_SYSTEM_PROMPT = """
You are an expert initial question generator.
Your goal is to start a productive conversation based on the provided context.

Guidelines:
1. Generate an open-ended but specific initial question
2. Make the question relevant to the provided context
3. Frame the question to elicit a detailed response
4. Avoid overly broad questions like "How can I help you?"
5. Ensure the question feels natural and conversational

Output should be a single, focused question without any additional commentary or explanation.
"""


class QuestionGenerationService:
    """Service for generating sequential questions."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance of the service."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize the question generation service with LangChain components."""
        # Ensure singleton pattern
        if QuestionGenerationService._instance is not None:
            raise RuntimeError("QuestionGenerationService is a singleton! Use get_instance() instead.")
        
        # Initialize base components
        self.llm = self._initialize_llm()
        self.message_repository = MessageRepository()
        self.conversation_repository = ConversationRepository()
        self.user_session_repository = UserSessionRepository()
        self.vector_search = VectorSearchService.get_instance()
        
        # Initialize prompt templates
        self.follow_up_question_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(QUESTION_GENERATION_SYSTEM_PROMPT),
            HumanMessagePromptTemplate.from_template(
                "Context: {context}\n\n"
                "Previous messages:\n{previous_messages}\n\n"
                "Generate the next question in this conversation:"
            )
        ])
        
        self.initial_question_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(INITIAL_QUESTION_GENERATION_SYSTEM_PROMPT),
            HumanMessagePromptTemplate.from_template(
                "Context: {context}\n\n"
                "Generate an initial question for this conversation:"
            )
        ])
        
        # Create chains
        self.follow_up_question_chain = self.follow_up_question_prompt | self.llm | StrOutputParser()
        self.initial_question_chain = self.initial_question_prompt | self.llm | StrOutputParser()
        
        QuestionGenerationService._instance = self
    
    def _initialize_llm(self) -> BaseChatModel:
        """Initialize the LLM with appropriate configuration."""
        # Use only OPENAI_MODEL_NAME for consistency
        model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        api_key = os.getenv("OPENAI_API_KEY")
        
        # Log API key presence (not the key itself)
        app_logger.info(f"Initializing LLM with model: {model_name}, API key present: {bool(api_key)}")
        
        if not api_key:
            app_logger.error("OPENAI_API_KEY environment variable is not set or empty")
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        return ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            openai_api_key=api_key
        )
    
    @measure_time
    async def generate_question(
        self, 
        db, 
        request: QuestionRequest
    ) -> QuestionResponse:
        """Generate a batch of sequential questions based on context and previous messages.
        
        Args:
            db: Database session
            request: Question request containing context and previous messages
            
        Returns:
            Generated question response with metadata and a batch of questions
        """
        # Get or create user session
        session_id, session = await self._get_or_create_session(db, request.user_id, request.context)
        
        # Get or create conversation
        conversation_id, conversation = await self._get_or_create_conversation(
            db, session_id, request.conversation_id, request.context
        )
        
        # Process previous messages and context
        previous_messages_formatted, has_previous_messages = self._format_previous_messages(
            request.previous_messages
        )
        
        # Get relevant context from vector database if available
        context = request.context or ""
        if has_previous_messages and context:
            # Enhance context with vector search
            last_user_message = self._get_last_user_message(request.previous_messages)
            if last_user_message:
                similar_contexts = await vector_db_service.search_similar(
                    last_user_message.content,
                    filter_params={"conversation_id": conversation_id},
                    limit=3
                )
                
                if similar_contexts:
                    enhanced_contexts = [
                        f"- {ctx['payload'].get('content', '')}" 
                        for ctx in similar_contexts 
                        if 'content' in ctx['payload']
                    ]
                    if enhanced_contexts:
                        context += "\n\nAdditional relevant information:\n" + "\n".join(enhanced_contexts)
        
        # Determine the starting question number
        question_count = await self.message_repository.count_by_conversation(
            db, conversation_id=conversation_id, message_type="question"
        )
        starting_question_number = question_count + 1
        
        # Define batch size (3-5 questions per batch)
        batch_size = 5 if not has_previous_messages else 3
        
        # Generate batch of questions
        if not has_previous_messages:
            # For initial batch, use the context only
            questions_batch, batch_metadata = await self._generate_question_batch(
                context, 
                "", 
                batch_size=batch_size,
                starting_question_number=starting_question_number
            )
        else:
            # For follow-up batches, use both context and previous messages
            questions_batch, batch_metadata = await self._generate_question_batch(
                context, 
                previous_messages_formatted, 
                batch_size=batch_size,
                starting_question_number=starting_question_number
            )
        
        # Create question items for the response
        question_items = []
        for q in questions_batch:
            # Store each question in the database
            message_data = MessageCreate(
                conversation_id=conversation_id,
                message_type="question",
                content=q["question_text"],
                metadata={
                    "generated": True,
                    "timestamp": datetime.now().isoformat(),
                    "question_number": q["question_number"],
                    "batch_number": 1 + (q["question_number"] - 1) // batch_size,
                    "importance_explanation": q.get("importance_explanation", ""),
                    "information_to_look_for": q.get("information_to_look_for", "")
                },
                sequence_number=await self.message_repository.get_next_sequence_number(db, conversation_id=conversation_id)
            )
            
            question_msg = await self.message_repository.create(db, obj_in=message_data)
            
            # Store question text in vector database for future context
            await vector_db_service.store_embedding(
                text=q["question_text"],
                metadata={
                    "content": q["question_text"],
                    "type": "question",
                    "question_number": q["question_number"],
                    "conversation_id": conversation_id,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            question_items.append(
                QuestionItem(
                    question_text=q["question_text"],
                    question_number=q["question_number"],
                    metadata={
                        "importance": q.get("importance_explanation", ""),
                        "information_to_look_for": q.get("information_to_look_for", "")
                    }
                )
            )
        
        # Get the current question (first question in the batch)
        current_question = questions_batch[0]["question_text"]
        
        app_logger.info(f"Generated question batch for conversation {conversation_id}: {len(question_items)} questions")
        
        # Return the response with the batch of questions
        return QuestionResponse(
            current_question=current_question,
            questions=question_items,
            conversation_id=conversation_id,
            session_id=session_id,
            current_question_number=starting_question_number,
            total_questions_in_batch=len(question_items),
            total_questions_estimated=batch_metadata.get("total_questions_estimated", 8),
            next_batch_needed=batch_metadata.get("next_batch_needed", True),
            metadata={
                "context_enhanced": bool(similar_contexts) if has_previous_messages and context else False,
                "question_type": "initial" if not has_previous_messages else "follow_up",
                "timestamp": datetime.now().isoformat(),
                "batch_metadata": batch_metadata
            }
        )
    
    async def _get_or_create_session(
        self, 
        db, 
        user_id: Optional[str], 
        context: Optional[str]
    ) -> Tuple[str, Any]:
        """Get existing session or create a new one."""
        session = None
        if user_id:
            session = await self.user_session_repository.get_by_user_identifier(db, user_identifier=user_id)
        
        if not session:
            session_data = UserSessionCreate(
                user_identifier=user_id,
                context=context,
                is_active=True
            )
            session = await self.user_session_repository.create(db, obj_in=session_data)
            app_logger.info(f"Created new user session with ID {session.id}")
        
        return session.id, session
    
    async def _get_or_create_conversation(
        self, 
        db, 
        session_id: str, 
        conversation_id: Optional[str], 
        context: Optional[str]
    ) -> Tuple[str, Any]:
        """Get existing conversation or create a new one."""
        conversation = None
        if conversation_id:
            conversation = await self.conversation_repository.get(db, id=conversation_id)
        
        if not conversation:
            # Try to get active conversation for this session
            conversation = await self.conversation_repository.get_active_by_user_session_id(
                db, user_session_id=session_id
            )
            
        if not conversation:
            # Create new conversation
            conversation_data = ConversationCreate(
                user_session_id=session_id,
                topic=context[:50] if context else "New conversation",
                is_active=True
            )
            conversation = await self.conversation_repository.create(db, obj_in=conversation_data)
            app_logger.info(f"Created new conversation with ID {conversation.id}")
        
        return conversation.id, conversation
    
    def _format_previous_messages(self, messages: Optional[List[MessageItem]]) -> Tuple[str, bool]:
        """Format previous messages for prompt."""
        if not messages:
            return "", False
        
        formatted_messages = []
        for msg in messages:
            role = msg.role.capitalize()
            formatted_messages.append(f"{role}: {msg.content}")
        
        return "\n".join(formatted_messages), True
    
    def _get_last_user_message(self, messages: Optional[List[MessageItem]]) -> Optional[MessageItem]:
        """Get the last user message from the conversation."""
        if not messages:
            return None
        
        for msg in reversed(messages):
            if msg.role.lower() == "user":
                return msg
        
        return None
    
    async def _generate_initial_question(self, context: str) -> str:
        """Generate an initial question based on context."""
        if not context:
            context = "General conversation"
            
        response = await self.initial_question_chain.ainvoke({"context": context})
        return response.strip()
    
    async def _generate_follow_up_question(self, context: str, previous_messages: str) -> str:
        """Generate a follow-up question based on context and previous messages."""
        if not context:
            context = "Continue the conversation naturally"
            
        response = await self.follow_up_question_chain.ainvoke({
            "context": context,
            "previous_messages": previous_messages
        })
        return response.strip()

    # Add this new method to generate multiple questions
    async def _generate_question_batch(
        self, 
        context: str, 
        previous_messages: str = "",
        batch_size: int = 5,
        starting_question_number: int = 1
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Generate a batch of follow-up questions with metadata.
        
        Args:
            context: Context information for question generation
            previous_messages: Formatted previous messages as context
            batch_size: Number of questions to generate in this batch
            starting_question_number: Starting question number for this batch
            
        Returns:
            Tuple of (list of question dicts, batch metadata)
        """
        # Create a prompt that asks for multiple questions
        batch_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                """You are an expert question generator for a sequential questioning system.
                Your goal is to generate a batch of {batch_size} thoughtful, relevant questions based on the provided context.
                
                These questions should:
                1. Be clear, specific, and designed to gather useful information
                2. Follow a logical progression, with each question building on previous ones
                3. Cover different aspects of the topic to get a comprehensive understanding
                4. Be diverse in nature (avoid repetition)
                5. Be numbered sequentially
                6. Be designed for the user to answer all questions in a single response
                
                For each question, also provide:
                - An explanation of why this question is important to ask
                - A suggestion for what kind of information to look for in the answer
                
                The user will see all questions at once in a numbered list format, and will be expected to answer all of them in a single response using the same numbering format.
                """
            ),
            HumanMessagePromptTemplate.from_template(
                "Context: {context}\n\n"
                "Previous messages (if any):\n{previous_messages}\n\n"
                "Generate {batch_size} sequential questions starting with question #{starting_question_number}. "
                "Format your response as a JSON array of question objects, each with 'question_text', 'importance_explanation', "
                "and 'information_to_look_for' fields."
            )
        ])
        
        # Call LLM with the batch prompt
        response = await self.llm.ainvoke(
            batch_prompt.format_messages(
                context=context,
                previous_messages=previous_messages if previous_messages else "No previous messages",
                batch_size=batch_size,
                starting_question_number=starting_question_number
            )
        )
        
        # Extract the content and parse JSON
        try:
            content = response.content
            # Find the JSON part if it's mixed with other text
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            questions_batch = json.loads(content)
            
            # If not in expected format, try to extract and reformat
            if not isinstance(questions_batch, list):
                if "questions" in questions_batch:
                    questions_batch = questions_batch["questions"]
                else:
                    # Create a list from the parsed object
                    questions_batch = [questions_batch]
            
            # Ensure each question has the required fields
            for i, q in enumerate(questions_batch):
                if "question_text" not in q:
                    # Try to find a key that might contain the question text
                    for key in q.keys():
                        if "question" in key.lower():
                            q["question_text"] = q[key]
                            break
                    # If still not found, use a default
                    if "question_text" not in q:
                        q["question_text"] = f"Question #{starting_question_number + i}"
                
                # Add question number if not present
                if "question_number" not in q:
                    q["question_number"] = starting_question_number + i
            
            # Limit to the requested batch size if we got more
            questions_batch = questions_batch[:batch_size]
            
            # If we got fewer questions than requested, generate simple ones to fill the gap
            while len(questions_batch) < batch_size:
                questions_batch.append({
                    "question_text": f"Can you provide more details about your {context.split()[0] if context else 'goals'}?",
                    "question_number": starting_question_number + len(questions_batch),
                    "importance_explanation": "This will help gather more specific information.",
                    "information_to_look_for": "Additional context and clarification."
                })
            
            # Generate batch metadata
            batch_metadata = {
                "batch_size": len(questions_batch),
                "starting_question_number": starting_question_number,
                "ending_question_number": starting_question_number + len(questions_batch) - 1,
                "generated_at": datetime.now().isoformat(),
                "next_batch_needed": True  # Default assumption
            }
            
            # Let's ask if more questions might be needed after this batch
            metadata_prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(
                    """Based on the context and questions generated so far, determine:
                    1. Whether more question batches would likely be needed after this one
                    2. Approximately how many total questions might be appropriate for this topic
                    
                    Return your answer as JSON with these fields:
                    - next_batch_needed: boolean
                    - total_questions_estimated: integer
                    """
                ),
                HumanMessagePromptTemplate.from_template(
                    "Context: {context}\n\n"
                    "Previous messages:\n{previous_messages}\n\n"
                    "Current batch of questions (questions {starting_number} to {ending_number}):\n{generated_questions}\n\n"
                    "Provide metadata about whether more questions would be needed:"
                )
            ])
            
            metadata_response = await self.llm.ainvoke(
                metadata_prompt.format_messages(
                    context=context,
                    previous_messages=previous_messages if previous_messages else "No previous messages",
                    starting_number=starting_question_number,
                    ending_number=starting_question_number + len(questions_batch) - 1,
                    generated_questions="\n".join([f"{q['question_number']}. {q['question_text']}" for q in questions_batch])
                )
            )
            
            try:
                content = metadata_response.content
                # Find the JSON part if it's mixed with other text
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                metadata_json = json.loads(content)
                
                # Update batch metadata with LLM's assessment
                if "next_batch_needed" in metadata_json:
                    batch_metadata["next_batch_needed"] = metadata_json["next_batch_needed"]
                if "total_questions_estimated" in metadata_json:
                    batch_metadata["total_questions_estimated"] = metadata_json["total_questions_estimated"]
            except Exception as e:
                app_logger.warning(f"Error parsing metadata JSON: {str(e)}")
                # Use default values if parsing fails
                batch_metadata["next_batch_needed"] = starting_question_number + len(questions_batch) < 8
                batch_metadata["total_questions_estimated"] = max(starting_question_number + len(questions_batch) + 2, 8)
            
            return questions_batch, batch_metadata
            
        except Exception as e:
            app_logger.error(f"Error processing batch questions: {str(e)}")
            # Fallback to simpler question generation
            fallback_questions = []
            for i in range(batch_size):
                q_num = starting_question_number + i
                if i == 0:
                    question = f"What are your main goals related to {context.split()[0] if context else 'this topic'}?"
                elif i == 1:
                    question = f"What challenges do you anticipate in achieving these goals?"
                elif i == 2:
                    question = f"What resources do you have available to help you with these goals?"
                elif i == 3:
                    question = f"How will you measure your progress toward these goals?"
                else:
                    question = f"What else would you like to share about your {context.split()[0] if context else 'goals'}?"
                
                fallback_questions.append({
                    "question_text": question,
                    "question_number": q_num,
                    "importance_explanation": "This is an essential question to understand your situation.",
                    "information_to_look_for": "Specific details and context."
                })
            
            fallback_metadata = {
                "batch_size": len(fallback_questions),
                "starting_question_number": starting_question_number,
                "ending_question_number": starting_question_number + len(fallback_questions) - 1,
                "generated_at": datetime.now().isoformat(),
                "next_batch_needed": starting_question_number + len(fallback_questions) < 8,
                "total_questions_estimated": max(starting_question_number + len(fallback_questions) + 2, 8),
                "fallback_generation": True
            }
            
            return fallback_questions, fallback_metadata


# Create question generation service instance
question_generation_service = QuestionGenerationService() 
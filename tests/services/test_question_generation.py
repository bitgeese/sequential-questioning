import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from app.services.question_generation import QuestionGenerationService
from app.schemas.question_generation import QuestionRequest, MessageItem


@pytest.fixture
def mock_langchain():
    """Mock LangChain components."""
    with patch("app.services.question_generation.LLMChain") as mock_chain:
        # Set up the chain mock
        mock_chain_instance = MagicMock()
        mock_chain_instance.arun = AsyncMock(return_value="What is your favorite programming language?")
        mock_chain.return_value = mock_chain_instance
        yield mock_chain


@pytest.fixture
def mock_vector_db():
    """Mock the vector DB service."""
    with patch("app.services.question_generation.vector_db_service") as mock_db:
        # Set up the mock
        mock_db.search_similar = AsyncMock(return_value=[
            {
                "id": "test-id-1",
                "score": 0.95,
                "payload": {
                    "content": "Python is a popular programming language",
                    "type": "answer",
                    "conversation_id": "test-conversation-id"
                }
            }
        ])
        mock_db.store_embedding = AsyncMock(return_value="test-embedding-id")
        yield mock_db


@pytest.fixture
def mock_repositories():
    """Mock the repositories."""
    with patch("app.services.question_generation.UserSessionRepository") as mock_user_repo, \
         patch("app.services.question_generation.ConversationRepository") as mock_conv_repo, \
         patch("app.services.question_generation.MessageRepository") as mock_msg_repo:
        
        # Mock user session repository
        mock_user_repo_instance = MagicMock()
        mock_user_repo_instance.get_by_user_identifier = AsyncMock(return_value=None)
        mock_user_repo_instance.create = AsyncMock(return_value=MagicMock(id="test-session-id"))
        mock_user_repo.return_value = mock_user_repo_instance
        
        # Mock conversation repository
        mock_conv_repo_instance = MagicMock()
        mock_conv_repo_instance.get = AsyncMock(return_value=None)
        mock_conv_repo_instance.get_active_by_user_session_id = AsyncMock(return_value=None)
        mock_conv_repo_instance.create = AsyncMock(return_value=MagicMock(id="test-conversation-id"))
        mock_conv_repo.return_value = mock_conv_repo_instance
        
        # Mock message repository
        mock_msg_repo_instance = MagicMock()
        mock_msg_repo_instance.create = AsyncMock(return_value=MagicMock())
        mock_msg_repo_instance.get_next_sequence_number = AsyncMock(return_value=1)
        mock_msg_repo.return_value = mock_msg_repo_instance
        
        yield mock_user_repo, mock_conv_repo, mock_msg_repo


@pytest.mark.asyncio
async def test_generate_initial_question(mock_langchain, mock_vector_db, mock_repositories):
    """Test generating an initial question."""
    # Create service
    service = QuestionGenerationService()
    
    # Replace the _initialize method to use our mocks
    service._initialize = lambda: None
    service.initial_question_chain = mock_langchain.return_value
    service.follow_up_question_chain = mock_langchain.return_value
    service.user_session_repo = mock_repositories[0].return_value
    service.conversation_repo = mock_repositories[1].return_value
    service.message_repo = mock_repositories[2].return_value
    
    # Create request
    request = QuestionRequest(
        user_id="test-user",
        context="Testing question generation"
    )
    
    # Generate question
    db_session = MagicMock()
    response = await service.generate_question(db_session, request)
    
    # Check response
    assert response is not None
    assert response.question == "What is your favorite programming language?"
    assert response.conversation_id == "test-conversation-id"
    assert response.session_id == "test-session-id"
    assert "metadata" in response.dict()
    
    # Check that repositories were called
    service.user_session_repo.create.assert_called_once()
    service.conversation_repo.create.assert_called_once()
    service.message_repo.create.assert_called_once()
    
    # Check that LangChain was called
    service.initial_question_chain.arun.assert_called_once()


@pytest.mark.asyncio
async def test_generate_follow_up_question(mock_langchain, mock_vector_db, mock_repositories):
    """Test generating a follow-up question."""
    # Create service
    service = QuestionGenerationService()
    
    # Replace the _initialize method to use our mocks
    service._initialize = lambda: None
    service.initial_question_chain = mock_langchain.return_value
    service.follow_up_question_chain = mock_langchain.return_value
    service.user_session_repo = mock_repositories[0].return_value
    service.conversation_repo = mock_repositories[1].return_value
    service.message_repo = mock_repositories[2].return_value
    
    # Create request with previous messages
    request = QuestionRequest(
        user_id="test-user",
        context="Testing question generation",
        conversation_id="existing-conversation-id",
        previous_messages=[
            MessageItem(
                role="user",
                content="I like programming in Python",
                timestamp=datetime.now()
            ),
            MessageItem(
                role="assistant",
                content="That's great! Python is versatile.",
                timestamp=datetime.now()
            )
        ]
    )
    
    # Mock conversation retrieval
    service.conversation_repo.get.return_value = MagicMock(id="existing-conversation-id")
    
    # Generate question
    db_session = MagicMock()
    response = await service.generate_question(db_session, request)
    
    # Check response
    assert response is not None
    assert response.question == "What is your favorite programming language?"
    
    # Check that vector DB was called for context enhancement
    service.conversation_repo.get.assert_called_once()
    mock_vector_db.search_similar.assert_called_once()
    
    # Check that follow-up question chain was used
    service.follow_up_question_chain.arun.assert_called_once() 
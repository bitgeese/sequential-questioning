import pytest
import json
from fastapi.testclient import TestClient
from app import create_app
from app.models.database import UserSessionRepository, ConversationRepository, MessageRepository
from app.models.user_session import UserSession
from app.models.question import Question
from app.repositories.question_repository import QuestionRepository
from app.repositories.user_session_repository import UserSessionRepository
from app.services.sequential_questioning_service import SequentialQuestioningService
from app.core.monitoring import Metrics

client = TestClient(create_app())

@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset metrics before each test."""
    Metrics().reset()
    yield

@pytest.fixture
def mock_questions():
    questions = [
        Question(
            id="q1",
            text="What is your name?",
            type="text",
            required=True,
            order=1
        ),
        Question(
            id="q2",
            text="How old are you?",
            type="number",
            required=True,
            order=2
        ),
        Question(
            id="q3",
            text="What is your favorite color?",
            type="text",
            required=False,
            order=3
        )
    ]
    
    repo = QuestionRepository()
    for q in questions:
        repo.add(q)
    
    return questions

@pytest.fixture
def cleanup_sessions():
    yield
    # Cleanup all created sessions
    session_repo = UserSessionRepository()
    session_repo.clear()

@pytest.fixture
def clean_repositories():
    """Clean repositories before and after each test."""
    # Setup
    user_repo = UserSessionRepository()
    conv_repo = ConversationRepository()
    msg_repo = MessageRepository()
    
    # Clear data
    user_repo.delete_all()
    conv_repo.delete_all()
    msg_repo.delete_all()
    
    yield
    
    # Teardown
    user_repo.delete_all()
    conv_repo.delete_all()
    msg_repo.delete_all()

@pytest.fixture
def app():
    """Create a test app instance."""
    return create_app()

def test_complete_questioning_flow(mock_questions, cleanup_sessions):
    """
    Test the complete flow of a sequential questioning session:
    1. Create a new session
    2. Get the first question
    3. Answer questions in sequence
    4. Verify session completion
    5. Verify metrics are recorded
    """
    # Step 1: Create a new session
    response = client.post("/api/sessions/")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    session_id = data["session_id"]
    
    # Step 2: Get the first question
    response = client.get(f"/api/sessions/{session_id}/questions/next")
    assert response.status_code == 200
    question = response.json()
    assert question["id"] == "q1"
    
    # Step 3a: Answer the first question
    answer_data = {"answer": "John Doe"}
    response = client.post(f"/api/sessions/{session_id}/questions/{question['id']}/answer", json=answer_data)
    assert response.status_code == 200
    
    # Get the next question
    response = client.get(f"/api/sessions/{session_id}/questions/next")
    assert response.status_code == 200
    question = response.json()
    assert question["id"] == "q2"
    
    # Step 3b: Answer the second question
    answer_data = {"answer": 30}
    response = client.post(f"/api/sessions/{session_id}/questions/{question['id']}/answer", json=answer_data)
    assert response.status_code == 200
    
    # Get the next question
    response = client.get(f"/api/sessions/{session_id}/questions/next")
    assert response.status_code == 200
    question = response.json()
    assert question["id"] == "q3"
    
    # Step 3c: Answer the third question
    answer_data = {"answer": "Blue"}
    response = client.post(f"/api/sessions/{session_id}/questions/{question['id']}/answer", json=answer_data)
    assert response.status_code == 200
    
    # Step 4: Verify session completion
    # Try to get the next question - should indicate no more questions
    response = client.get(f"/api/sessions/{session_id}/questions/next")
    assert response.status_code == 200
    data = response.json()
    assert data.get("completed") is True
    
    # Get the session answers
    response = client.get(f"/api/sessions/{session_id}/answers")
    assert response.status_code == 200
    answers = response.json()
    assert len(answers) == 3
    assert answers["q1"] == "John Doe"
    assert answers["q2"] == 30
    assert answers["q3"] == "Blue"
    
    # Step 5: Verify metrics
    metrics = Metrics().get_metrics()
    assert metrics["total_requests"] >= 7  # At least our 7 API calls
    assert "avg_response_time" in metrics
    assert metrics["success_count"] >= 7
    assert metrics["error_count"] == 0

def test_error_handling_required_questions(mock_questions, cleanup_sessions):
    """
    Test error handling for required questions:
    1. Create a new session
    2. Get the first question
    3. Try to skip a required question
    4. Verify error response
    """
    # Create a new session
    response = client.post("/api/sessions/")
    assert response.status_code == 200
    data = response.json()
    session_id = data["session_id"]
    
    # Get the first question
    response = client.get(f"/api/sessions/{session_id}/questions/next")
    assert response.status_code == 200
    question = response.json()
    
    # Try to get the next question without answering the first one
    response = client.get(f"/api/sessions/{session_id}/questions/next")
    assert response.status_code == 400
    
    # Verify metrics captured the error
    metrics = Metrics().get_metrics()
    assert metrics["error_count"] >= 1

def test_mcp_integration(mock_questions, cleanup_sessions):
    """
    Test the MCP integration using the MCP endpoint:
    1. Create a session through MCP
    2. Process a series of questions through MCP
    3. Verify results
    """
    # Create session through MCP
    mcp_request = {
        "action": "create_session"
    }
    response = client.post("/api/mcp", json=mcp_request)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    session_id = data["session_id"]
    
    # Get next question through MCP
    mcp_request = {
        "action": "get_next_question",
        "session_id": session_id
    }
    response = client.post("/api/mcp", json=mcp_request)
    assert response.status_code == 200
    data = response.json()
    assert "question" in data
    assert data["question"]["id"] == "q1"
    
    # Answer first question through MCP
    mcp_request = {
        "action": "answer_question",
        "session_id": session_id,
        "question_id": "q1",
        "answer": "Jane Smith"
    }
    response = client.post("/api/mcp", json=mcp_request)
    assert response.status_code == 200
    
    # Continue with the next questions
    # Get and answer second question
    mcp_request = {
        "action": "get_next_question",
        "session_id": session_id
    }
    response = client.post("/api/mcp", json=mcp_request)
    assert response.status_code == 200
    data = response.json()
    
    mcp_request = {
        "action": "answer_question",
        "session_id": session_id,
        "question_id": "q2",
        "answer": 25
    }
    response = client.post("/api/mcp", json=mcp_request)
    assert response.status_code == 200
    
    # Get and answer third question
    mcp_request = {
        "action": "get_next_question",
        "session_id": session_id
    }
    response = client.post("/api/mcp", json=mcp_request)
    assert response.status_code == 200
    data = response.json()
    
    mcp_request = {
        "action": "answer_question",
        "session_id": session_id,
        "question_id": "q3",
        "answer": "Green"
    }
    response = client.post("/api/mcp", json=mcp_request)
    assert response.status_code == 200
    
    # Get session summary through MCP
    mcp_request = {
        "action": "get_session_answers",
        "session_id": session_id
    }
    response = client.post("/api/mcp", json=mcp_request)
    assert response.status_code == 200
    data = response.json()
    
    assert "answers" in data
    answers = data["answers"]
    assert len(answers) == 3
    assert answers["q1"] == "Jane Smith"
    assert answers["q2"] == 25
    assert answers["q3"] == "Green"

def test_sequential_questioning_flow(app, clean_repositories):
    """
    Test the complete sequential questioning flow using the MCP endpoint:
    1. Start with a context
    2. Get an initial question
    3. Answer the question and get follow-up questions
    4. Verify conversation is tracked properly
    """
    with TestClient(app) as client:
        # Initial context for question generation
        context = "Customer support conversation about a product return"
        user_id = "test_user_123"
        
        # Step 1: Generate initial question
        request_data = {
            "userId": user_id,
            "context": context,
            "previousMessages": []
        }
        
        response = client.post("/mcp/sequential-questioning", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "question" in data
        assert "conversationId" in data
        assert "sessionId" in data
        
        conversation_id = data["conversationId"]
        session_id = data["sessionId"]
        
        # Step 2: Send a user reply and get follow-up question
        user_reply = "I received a damaged product and would like to return it"
        request_data = {
            "userId": user_id,
            "context": context,
            "previousMessages": [
                {"role": "assistant", "content": data["question"]},
                {"role": "user", "content": user_reply}
            ],
            "conversationId": conversation_id,
            "sessionId": session_id
        }
        
        response = client.post("/mcp/sequential-questioning", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "question" in data
        assert data["conversationId"] == conversation_id
        assert data["sessionId"] == session_id
        
        # Step 3: Continue the conversation with another exchange
        user_reply2 = "I purchased it last week from your online store"
        request_data = {
            "userId": user_id,
            "context": context,
            "previousMessages": [
                {"role": "assistant", "content": data["question"]},
                {"role": "user", "content": user_reply2}
            ],
            "conversationId": conversation_id,
            "sessionId": session_id
        }
        
        response = client.post("/mcp/sequential-questioning", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "question" in data
        assert data["conversationId"] == conversation_id
        assert data["sessionId"] == session_id
        
        # Step 4: Verify metrics
        metrics_response = client.get("/mcp-internal/monitoring/metrics")
        assert metrics_response.status_code == 200
        metrics = metrics_response.json()
        assert metrics["total_requests"] >= 3  # Our 3 API calls
        assert metrics["success_count"] >= 3
        
        # Step 5: Verify conversation data is stored correctly
        # Verify user session exists
        user_repo = UserSessionRepository()
        session = user_repo.get_by_id(session_id)
        assert session is not None
        assert session.user_id == user_id
        
        # Verify conversation exists
        conv_repo = ConversationRepository()
        conversation = conv_repo.get_by_id(conversation_id)
        assert conversation is not None
        assert conversation.session_id == session_id
        
        # Verify messages are stored
        msg_repo = MessageRepository()
        messages = msg_repo.get_by_conversation_id(conversation_id)
        assert len(messages) > 0  # Should have multiple messages from our exchange

def test_sequential_questioning_error_handling(app, clean_repositories):
    """
    Test error handling in the sequential questioning flow:
    1. Test missing required fields
    2. Test invalid conversation ID
    3. Test server errors during question generation
    """
    with TestClient(app) as client:
        # Test missing required fields
        request_data = {
            # Missing userId
            "context": "Test context",
            "previousMessages": []
        }
        
        response = client.post("/mcp/sequential-questioning", json=request_data)
        assert response.status_code == 422  # Validation error
        
        # Test with invalid conversation ID
        request_data = {
            "userId": "test_user",
            "context": "Test context",
            "previousMessages": [],
            "conversationId": "invalid_conversation_id",
            "sessionId": "invalid_session_id"
        }
        
        response = client.post("/mcp/sequential-questioning", json=request_data)
        assert response.status_code in [404, 400]  # Not found or bad request
        
        # Verify metrics captured the errors
        metrics_response = client.get("/mcp-internal/monitoring/metrics")
        assert metrics_response.status_code == 200
        metrics = metrics_response.json()
        assert metrics["error_count"] > 0 
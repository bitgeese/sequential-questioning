import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from app.schemas.question_generation import QuestionRequest, QuestionResponse, MessageItem


@pytest.fixture
def mock_question_generation_service():
    """Mock the question generation service."""
    with patch("app.mcp.sequential_questioning.question_generation_service") as mock_service:
        # Set up the mock
        mock_response = QuestionResponse(
            question="What is your favorite color?",
            conversation_id="mock-conversation-id",
            session_id="mock-session-id",
            metadata={"question_type": "initial"},
            next_question_type="follow_up",
            requires_followup=False
        )
        mock_service.generate_question.return_value = mock_response
        yield mock_service


def test_sequential_questioning_endpoint(test_client, mock_question_generation_service):
    """Test the sequential questioning MCP endpoint."""
    # Create a request
    request_data = {
        "user_id": "test-user",
        "conversation_id": None,
        "context": "Testing the sequential questioning endpoint",
        "previous_messages": [
            {
                "role": "user",
                "content": "Hello, I'm here to test the endpoint",
                "timestamp": datetime.now().isoformat()
            }
        ],
        "metadata": {"source": "test"}
    }
    
    # Make the request
    response = test_client.post("/mcp-internal/question", json=request_data)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "question" in data
    assert "conversation_id" in data
    assert "session_id" in data
    assert "metadata" in data
    
    # Check specific values
    assert data["question"] == "What is your favorite color?"
    assert data["conversation_id"] == "mock-conversation-id"
    assert data["session_id"] == "mock-session-id"
    
    # Check that the service was called with the right parameters
    mock_question_generation_service.generate_question.assert_called_once()
    call_args = mock_question_generation_service.generate_question.call_args[0]
    
    # First arg is db session, second is the request
    assert isinstance(call_args[1], QuestionRequest)
    assert call_args[1].user_id == "test-user"
    assert call_args[1].context == "Testing the sequential questioning endpoint"


def test_sequential_questioning_endpoint_error(test_client, mock_question_generation_service):
    """Test error handling in the sequential questioning MCP endpoint."""
    # Set up the mock to raise an exception
    mock_question_generation_service.generate_question.side_effect = Exception("Test error")
    
    # Create a request
    request_data = {
        "user_id": "test-user",
        "context": "Testing error handling"
    }
    
    # Make the request
    response = test_client.post("/mcp-internal/question", json=request_data)
    
    # Check response
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "Failed to generate question" in data["detail"] 
import pytest
from httpx import AsyncClient
import json
from unittest.mock import patch, MagicMock

from app.models.user_session import UserSession
from app.repositories.user_session_repository import UserSessionRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.core.monitoring import Metrics


@pytest.fixture
def user_data():
    return {
        "user_id": "test-user-123",
        "context": "Testing healthcare insurance benefits for a new employee",
        "previous_messages": []
    }


@pytest.mark.asyncio
async def test_end_to_end_question_flow(test_client: AsyncClient, user_data):
    """
    Test the complete sequential questioning flow from initial question to follow-up
    """
    # Make sure metrics are reset for this test
    Metrics().reset()
    
    # Step 1: Generate initial question
    initial_response = await test_client.post(
        "/mcp/sequential-questioning",
        json=user_data
    )
    assert initial_response.status_code == 200
    initial_data = initial_response.json()
    
    # Verify structure of response
    assert "question" in initial_data
    assert "conversation_id" in initial_data
    assert "session_id" in initial_data
    
    # Get the conversation ID for follow-up
    conversation_id = initial_data["conversation_id"]
    
    # Step 2: Add a simulated user response to the message
    user_answer = {
        "user_id": user_data["user_id"],
        "conversation_id": conversation_id,
        "message": "I'm interested in family coverage options."
    }
    
    # This would typically be done by a frontend client, saving message for conversation continuity
    # In a real scenario, there might be a separate endpoint for this
    
    # Step 3: Generate a follow-up question
    follow_up_data = {
        "user_id": user_data["user_id"],
        "context": user_data["context"],
        "conversation_id": conversation_id,
        "previous_messages": [
            {"role": "assistant", "content": initial_data["question"]},
            {"role": "user", "content": user_answer["message"]}
        ]
    }
    
    follow_up_response = await test_client.post(
        "/mcp/sequential-questioning",
        json=follow_up_data
    )
    
    assert follow_up_response.status_code == 200
    follow_up_data = follow_up_response.json()
    
    # Verify the follow-up question structure
    assert "question" in follow_up_data
    assert "conversation_id" in follow_up_data
    assert follow_up_data["conversation_id"] == conversation_id
    assert "session_id" in follow_up_data
    
    # Step 4: Check monitoring metrics to verify request tracking
    metrics_response = await test_client.get("/mcp-internal/monitoring/metrics")
    assert metrics_response.status_code == 200
    
    metrics_data = metrics_response.json()
    assert metrics_data["total_requests"] >= 2  # At least our two question requests
    assert metrics_data["success_count"] >= 2
    assert "avg_response_time" in metrics_data
    assert "status_codes" in metrics_data


@pytest.mark.asyncio
async def test_persistence_across_requests(test_client: AsyncClient, user_data):
    """
    Test that user sessions and conversations persist correctly across multiple requests
    """
    # Step 1: Generate initial question and capture IDs
    initial_response = await test_client.post(
        "/mcp/sequential-questioning",
        json=user_data
    )
    assert initial_response.status_code == 200
    initial_data = initial_response.json()
    
    session_id = initial_data["session_id"]
    conversation_id = initial_data["conversation_id"]
    
    # Step 2: Make a second request with the same conversation_id
    follow_up_data = {
        "user_id": user_data["user_id"],
        "context": user_data["context"],
        "conversation_id": conversation_id,
        "previous_messages": [
            {"role": "assistant", "content": initial_data["question"]},
            {"role": "user", "content": "Yes, I have a question about deductibles"}
        ]
    }
    
    follow_up_response = await test_client.post(
        "/mcp/sequential-questioning",
        json=follow_up_data
    )
    
    assert follow_up_response.status_code == 200
    follow_up_data = follow_up_response.json()
    
    # Verify the same conversation and session are used
    assert follow_up_data["conversation_id"] == conversation_id
    assert follow_up_data["session_id"] == session_id


@pytest.mark.asyncio
async def test_new_conversation_in_same_session(test_client: AsyncClient, user_data):
    """
    Test starting a new conversation within the same user session
    """
    # Step 1: Generate initial question for first conversation
    initial_response = await test_client.post(
        "/mcp/sequential-questioning",
        json=user_data
    )
    initial_data = initial_response.json()
    session_id = initial_data["session_id"]
    
    # Step 2: Start a new conversation (omit conversation_id) in the same session
    new_conversation_data = {
        "user_id": user_data["user_id"],
        "context": "New topic about retirement benefits",
        "previous_messages": []
    }
    
    new_conv_response = await test_client.post(
        "/mcp/sequential-questioning",
        json=new_conversation_data
    )
    
    assert new_conv_response.status_code == 200
    new_conv_data = new_conv_response.json()
    
    # Verify we get the same session but a different conversation
    assert new_conv_data["session_id"] == session_id
    assert new_conv_data["conversation_id"] != initial_data["conversation_id"] 
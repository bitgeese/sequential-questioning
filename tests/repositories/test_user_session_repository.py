import pytest
from uuid import uuid4

from app.repositories.user_session import UserSessionRepository
from app.schemas.user_session import UserSessionCreate, UserSessionUpdate


@pytest.mark.asyncio
async def test_user_session_repository_create(db_session):
    """Test creating a user session via repository."""
    repo = UserSessionRepository()
    
    session_data = UserSessionCreate(
        user_identifier="test_repo_user",
        context="Test repository context",
        is_active=True
    )
    
    created_session = await repo.create(db_session, obj_in=session_data)
    
    assert created_session is not None
    assert created_session.user_identifier == "test_repo_user"
    assert created_session.context == "Test repository context"
    assert created_session.is_active is True
    assert created_session.id is not None


@pytest.mark.asyncio
async def test_user_session_repository_get(db_session):
    """Test retrieving a user session via repository."""
    repo = UserSessionRepository()
    
    # Create a session first
    session_data = UserSessionCreate(
        user_identifier="get_repo_user",
        context="Get repository context",
        is_active=True
    )
    
    created_session = await repo.create(db_session, obj_in=session_data)
    session_id = created_session.id
    
    # Get the session
    retrieved_session = await repo.get(db_session, id=session_id)
    
    assert retrieved_session is not None
    assert retrieved_session.id == session_id
    assert retrieved_session.user_identifier == "get_repo_user"


@pytest.mark.asyncio
async def test_user_session_repository_update(db_session):
    """Test updating a user session via repository."""
    repo = UserSessionRepository()
    
    # Create a session first
    session_data = UserSessionCreate(
        user_identifier="update_repo_user",
        context="Original repository context",
        is_active=True
    )
    
    created_session = await repo.create(db_session, obj_in=session_data)
    
    # Update the session
    update_data = UserSessionUpdate(
        context="Updated repository context",
        is_active=False
    )
    
    updated_session = await repo.update(db_session, db_obj=created_session, obj_in=update_data)
    
    assert updated_session is not None
    assert updated_session.context == "Updated repository context"
    assert updated_session.is_active is False
    assert updated_session.user_identifier == "update_repo_user"  # Should not change


@pytest.mark.asyncio
async def test_user_session_repository_delete(db_session):
    """Test deleting a user session via repository."""
    repo = UserSessionRepository()
    
    # Create a session first
    session_data = UserSessionCreate(
        user_identifier="delete_repo_user",
        context="Delete repository context",
        is_active=True
    )
    
    created_session = await repo.create(db_session, obj_in=session_data)
    session_id = created_session.id
    
    # Delete the session
    deleted_session = await repo.delete(db_session, id=session_id)
    
    assert deleted_session is not None
    assert deleted_session.id == session_id
    
    # Try to retrieve the deleted session
    retrieved_session = await repo.get(db_session, id=session_id)
    assert retrieved_session is None


@pytest.mark.asyncio
async def test_user_session_repository_get_by_user_identifier(db_session):
    """Test getting a user session by user identifier."""
    repo = UserSessionRepository()
    
    # Create a session first
    session_data = UserSessionCreate(
        user_identifier="unique_user_identifier",
        context="User identifier context",
        is_active=True
    )
    
    await repo.create(db_session, obj_in=session_data)
    
    # Get the session by user identifier
    retrieved_session = await repo.get_by_user_identifier(
        db_session, user_identifier="unique_user_identifier"
    )
    
    assert retrieved_session is not None
    assert retrieved_session.user_identifier == "unique_user_identifier"


@pytest.mark.asyncio
async def test_user_session_repository_get_active_sessions(db_session):
    """Test getting all active user sessions."""
    repo = UserSessionRepository()
    
    # Create some active and inactive sessions
    for i in range(3):
        session_data = UserSessionCreate(
            user_identifier=f"active_user_{i}",
            context=f"Active context {i}",
            is_active=True
        )
        await repo.create(db_session, obj_in=session_data)
        
    for i in range(2):
        session_data = UserSessionCreate(
            user_identifier=f"inactive_user_{i}",
            context=f"Inactive context {i}",
            is_active=False
        )
        await repo.create(db_session, obj_in=session_data)
    
    # Get active sessions
    active_sessions = await repo.get_active_sessions(db_session)
    
    # There might be more active sessions from other tests, so we just check there are at least 3
    assert len(active_sessions) >= 3
    assert all(session.is_active for session in active_sessions)


@pytest.mark.asyncio
async def test_user_session_repository_deactivate_session(db_session):
    """Test deactivating a user session."""
    repo = UserSessionRepository()
    
    # Create an active session
    session_data = UserSessionCreate(
        user_identifier="deactivate_user",
        context="Deactivate context",
        is_active=True
    )
    
    created_session = await repo.create(db_session, obj_in=session_data)
    session_id = created_session.id
    
    # Deactivate the session
    deactivated_session = await repo.deactivate_session(db_session, id=session_id)
    
    assert deactivated_session is not None
    assert deactivated_session.id == session_id
    assert deactivated_session.is_active is False 
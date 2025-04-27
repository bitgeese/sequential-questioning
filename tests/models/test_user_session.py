import pytest
from sqlalchemy.future import select

from app.models.user_session import UserSession


@pytest.mark.asyncio
async def test_user_session_create(db_session):
    """Test creating a user session."""
    # Create a new user session
    user_session = UserSession(
        user_identifier="test_user",
        context="Test context",
        is_active=True
    )
    
    db_session.add(user_session)
    await db_session.commit()
    
    # Retrieve the user session from the database
    result = await db_session.execute(select(UserSession).where(UserSession.user_identifier == "test_user"))
    retrieved_session = result.scalars().first()
    
    # Assert that the session was created and has the correct attributes
    assert retrieved_session is not None
    assert retrieved_session.user_identifier == "test_user"
    assert retrieved_session.context == "Test context"
    assert retrieved_session.is_active is True
    assert retrieved_session.created_at is not None
    assert retrieved_session.updated_at is not None


@pytest.mark.asyncio
async def test_user_session_update(db_session):
    """Test updating a user session."""
    # Create a new user session
    user_session = UserSession(
        user_identifier="update_user",
        context="Original context",
        is_active=True
    )
    
    db_session.add(user_session)
    await db_session.commit()
    
    # Update the user session
    user_session.context = "Updated context"
    user_session.is_active = False
    await db_session.commit()
    
    # Retrieve the updated user session
    result = await db_session.execute(select(UserSession).where(UserSession.user_identifier == "update_user"))
    updated_session = result.scalars().first()
    
    # Assert that the session was updated
    assert updated_session is not None
    assert updated_session.context == "Updated context"
    assert updated_session.is_active is False


@pytest.mark.asyncio
async def test_user_session_delete(db_session):
    """Test deleting a user session."""
    # Create a new user session
    user_session = UserSession(
        user_identifier="delete_user",
        context="Delete context",
        is_active=True
    )
    
    db_session.add(user_session)
    await db_session.commit()
    
    # Delete the user session
    await db_session.delete(user_session)
    await db_session.commit()
    
    # Try to retrieve the deleted user session
    result = await db_session.execute(select(UserSession).where(UserSession.user_identifier == "delete_user"))
    deleted_session = result.scalars().first()
    
    # Assert that the session was deleted
    assert deleted_session is None 
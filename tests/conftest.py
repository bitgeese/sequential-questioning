import asyncio
import os
from typing import Generator, AsyncGenerator
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.models.database import Base, get_db
from app.core.config import get_settings, Settings


# Test settings fixture
@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Override settings for tests."""
    os.environ["APP_NAME"] = "Sequential Questioning MCP Server Test"
    os.environ["APP_VERSION"] = "0.1.0-test"
    os.environ["DEBUG"] = "True"
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
    os.environ["QDRANT_HOST"] = "localhost"
    os.environ["QDRANT_PORT"] = "6333"
    os.environ["QDRANT_COLLECTION_NAME"] = "test_sequential_questioning"
    os.environ["OPENAI_API_KEY"] = "sk-test-key"
    os.environ["LLM_MODEL"] = "gpt-4-turbo"
    os.environ["SECRET_KEY"] = "test-secret-key"
    
    return get_settings()


# Test database fixture
@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///./test.db",
        echo=False,
        future=True,
    )
    return engine


@pytest.fixture(scope="session")
async def test_db_setup(test_engine):
    """Set up test database tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(test_engine, test_db_setup) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for tests."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


# Override the database dependency
@pytest.fixture
def override_get_db(db_session):
    """Override the get_db dependency."""
    async def _override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


# Test client fixture
@pytest.fixture
def test_client(override_get_db, test_settings) -> Generator[TestClient, None, None]:
    """Create a test client for the app."""
    with TestClient(app) as client:
        yield client


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close() 
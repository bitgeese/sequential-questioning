from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Convert SQLite URL to async version if needed
if DATABASE_URL.startswith("sqlite://"):
    # SQLite URL with parameters
    if DATABASE_URL == "sqlite:///./app.db":
        # Default local development database
        ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./app.db"
    else:
        # Custom SQLite URL
        ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
elif DATABASE_URL.startswith("postgresql://"):
    # For PostgreSQL, use the asyncpg driver for async operations
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    # PostgreSQL or other database
    ASYNC_DATABASE_URL = DATABASE_URL

# Create async engine
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    future=True,
)

# Create sync engine for Alembic
sync_engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

# Create session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)

# Create base class for models
Base = declarative_base()


# Dependency to get database session
async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close() 
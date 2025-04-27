from fastapi import APIRouter

from app.api.endpoints import sessions, conversations, messages

# Create API router
api_router = APIRouter(prefix="/api")

# Include specific routers
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"]) 
from fastapi import APIRouter

from app.mcp.sequential_questioning import router as sequential_questioning_router
from app.mcp.monitoring import router as monitoring_router

# Create MCP router
mcp_router = APIRouter(prefix="/mcp-internal")

# Include specific routers
mcp_router.include_router(sequential_questioning_router, tags=["mcp"])
mcp_router.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"]) 
from fastapi import FastAPI, Depends
from fastapi_mcp import FastApiMCP

from app.core.config import get_settings, Settings
from app.api import api_router
from app.mcp import mcp_router
from app.core.monitoring import metrics
from app.core.logging import app_logger

# Create FastAPI app
def create_app() -> FastAPI:
    # Get settings
    settings = get_settings()
    
    # Initialize application
    app = FastAPI(
        title=settings.APP_NAME,
        description="A Sequential Questioning MCP Server for facilitating multi-round questioning",
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
    )
    
    # Setup API routes
    app.include_router(api_router)
    
    # Setup MCP routes (outside of MCP server)
    app.include_router(mcp_router)
    
    # Initialize MCP server
    mcp = FastApiMCP(
        app,
        name=f"{settings.APP_NAME} MCP",
        include_tags=["mcp"],  # Only expose endpoints with the 'mcp' tag
        include_operations=[
            "sequential_questioning",
            "sequential_questioning_follow_up",
            "sequential_questioning_automatic"
        ]  # Use only operation IDs for tool names, avoiding hyphens
    )
    
    # Mount MCP server
    mcp.mount()
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        app_logger.info("Health check request received")
        return {"status": "ok", "version": settings.APP_VERSION}
    
    # Log application startup
    app_logger.info(f"Application {settings.APP_NAME} v{settings.APP_VERSION} started")
    return app

# Create app instance
app = create_app() 
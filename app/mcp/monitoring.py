from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any

from app.core.monitoring import metrics
from app.core.logging import app_logger

router = APIRouter(tags=["monitoring"])


class MetricsResponse(BaseModel):
    """Response model for metrics endpoint."""
    uptime_seconds: float
    total_requests: int
    total_errors: int
    error_rate: float
    avg_response_time_ms: float
    endpoints: Dict[str, Any]


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get current application metrics."""
    app_logger.info("Retrieving application metrics")
    return metrics.get_metrics()


@router.post("/metrics/reset")
async def reset_metrics():
    """Reset all metrics."""
    app_logger.info("Resetting application metrics")
    metrics.reset_metrics()
    return {"status": "success", "message": "Metrics reset successfully"} 
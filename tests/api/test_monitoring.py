import pytest
from fastapi.testclient import TestClient

from app.core.monitoring import metrics


def test_get_metrics(test_client):
    """Test getting metrics from the monitoring API."""
    # Reset metrics to ensure a clean state
    metrics.reset_metrics()
    
    # Make a request to gather some metrics
    test_client.get("/health")
    
    # Get metrics
    response = test_client.get("/mcp-internal/monitoring/metrics")
    
    # Check response
    assert response.status_code == 200
    
    # Check response data structure
    data = response.json()
    assert "uptime_seconds" in data
    assert "total_requests" in data
    assert "total_errors" in data
    assert "error_rate" in data
    assert "avg_response_time_ms" in data
    assert "endpoints" in data
    
    # Check specific metrics
    assert data["total_requests"] >= 1  # At least our health check request
    assert isinstance(data["endpoints"], dict)


def test_reset_metrics(test_client):
    """Test resetting metrics via the API."""
    # Make a request to gather some metrics
    test_client.get("/health")
    
    # Check metrics before reset
    before_response = test_client.get("/mcp-internal/monitoring/metrics")
    before_data = before_response.json()
    assert before_data["total_requests"] >= 1
    
    # Reset metrics
    reset_response = test_client.post("/mcp-internal/monitoring/reset")
    assert reset_response.status_code == 200
    assert reset_response.json() == {"status": "success", "message": "Metrics reset successfully"}
    
    # Check metrics after reset
    after_response = test_client.get("/mcp-internal/monitoring/metrics")
    after_data = after_response.json()
    assert after_data["total_requests"] == 0  # Should be reset to 0 
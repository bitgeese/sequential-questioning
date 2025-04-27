import time
import statistics
import concurrent.futures
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.monitoring import Metrics

@pytest.fixture(scope="module")
def test_client():
    with TestClient(app) as client:
        yield client

def make_request(client, user_id="test_user", context="test context"):
    """Helper function to make a request to the sequential questioning endpoint"""
    start_time = time.time()
    response = client.post(
        "/mcp/sequential-questioning", 
        json={
            "user_id": user_id,
            "context": context,
            "previous_messages": []
        }
    )
    end_time = time.time()
    return {
        "status_code": response.status_code,
        "response_time": end_time - start_time,
        "success": response.status_code == 200
    }

def test_sequential_questioning_single_request(test_client):
    """Test a single request to establish baseline performance"""
    # Reset metrics
    test_client.post("/mcp-internal/monitoring/reset")
    
    # Make a single request
    result = make_request(test_client)
    
    # Assertions
    assert result["status_code"] == 200
    assert result["response_time"] > 0
    
    # Check metrics
    metrics_response = test_client.get("/mcp-internal/monitoring/metrics")
    metrics = metrics_response.json()
    
    assert metrics["total_requests"] == 1
    assert metrics["successful_requests"] == 1
    assert len(metrics["response_times"]) == 1

def test_sequential_questioning_concurrent_load(test_client):
    """Test the endpoint under concurrent load with multiple requests"""
    # Reset metrics
    test_client.post("/mcp-internal/monitoring/reset")
    
    # Number of concurrent requests
    n_requests = 5
    
    # Make concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_requests) as executor:
        futures = [executor.submit(make_request, test_client, f"user_{i}", f"context for user {i}") 
                  for i in range(n_requests)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # Analyze results
    response_times = [result["response_time"] for result in results]
    success_count = sum(1 for result in results if result["success"])
    
    # Log performance metrics
    print(f"\nLoad Test Results:")
    print(f"Total Requests: {n_requests}")
    print(f"Successful Requests: {success_count}")
    print(f"Failure Rate: {(n_requests - success_count) / n_requests * 100:.2f}%")
    print(f"Avg Response Time: {statistics.mean(response_times):.4f}s")
    print(f"Min Response Time: {min(response_times):.4f}s")
    print(f"Max Response Time: {max(response_times):.4f}s")
    if len(response_times) > 1:
        print(f"Std Dev Response Time: {statistics.stdev(response_times):.4f}s")
    
    # Assertions
    assert success_count == n_requests, f"Expected all requests to succeed, but got {success_count}/{n_requests}"
    
    # Check metrics
    metrics_response = test_client.get("/mcp-internal/monitoring/metrics")
    metrics = metrics_response.json()
    
    assert metrics["total_requests"] == n_requests
    assert metrics["successful_requests"] == n_requests
    assert len(metrics["response_times"]) == n_requests

def test_sequential_questioning_sequential_load(test_client):
    """Test the endpoint under sequential load with multiple requests"""
    # Reset metrics
    test_client.post("/mcp-internal/monitoring/reset")
    
    # Number of sequential requests
    n_requests = 3
    
    # Make sequential requests
    results = []
    for i in range(n_requests):
        result = make_request(test_client, f"user_{i}", f"context for user {i}")
        results.append(result)
    
    # Analyze results
    response_times = [result["response_time"] for result in results]
    success_count = sum(1 for result in results if result["success"])
    
    # Log performance metrics
    print(f"\nSequential Load Test Results:")
    print(f"Total Requests: {n_requests}")
    print(f"Successful Requests: {success_count}")
    print(f"Failure Rate: {(n_requests - success_count) / n_requests * 100:.2f}%")
    print(f"Avg Response Time: {statistics.mean(response_times):.4f}s")
    print(f"Min Response Time: {min(response_times):.4f}s")
    print(f"Max Response Time: {max(response_times):.4f}s")
    if len(response_times) > 1:
        print(f"Std Dev Response Time: {statistics.stdev(response_times):.4f}s")
    
    # Assertions
    assert success_count == n_requests, f"Expected all requests to succeed, but got {success_count}/{n_requests}"
    
    # Check metrics
    metrics_response = test_client.get("/mcp-internal/monitoring/metrics")
    metrics = metrics_response.json()
    
    assert metrics["total_requests"] == n_requests
    assert metrics["successful_requests"] == n_requests
    assert len(metrics["response_times"]) == n_requests 
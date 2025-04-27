import time
import functools
from typing import Callable, Any, Dict, Optional
import json
from datetime import datetime

from app.core.logging import app_logger


class Metrics:
    """Simple metrics collection for the application."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one metrics instance."""
        if cls._instance is None:
            cls._instance = super(Metrics, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize metrics storage."""
        self.metrics = {
            "requests": 0,
            "errors": 0,
            "response_times": [],
            "endpoints": {},
            "start_time": time.time()
        }
    
    def track_request(self, endpoint: str, response_time: float, status_code: int):
        """Track a request to an endpoint.
        
        Args:
            endpoint: The endpoint that was called
            response_time: The time taken to respond in milliseconds
            status_code: The HTTP status code returned
        """
        self.metrics["requests"] += 1
        self.metrics["response_times"].append(response_time)
        
        # Track by endpoint
        if endpoint not in self.metrics["endpoints"]:
            self.metrics["endpoints"][endpoint] = {
                "requests": 0,
                "errors": 0,
                "response_times": [],
            }
        
        self.metrics["endpoints"][endpoint]["requests"] += 1
        self.metrics["endpoints"][endpoint]["response_times"].append(response_time)
        
        # Track errors
        if status_code >= 400:
            self.metrics["errors"] += 1
            self.metrics["endpoints"][endpoint]["errors"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics with calculated statistics.
        
        Returns:
            Dictionary of metrics
        """
        uptime = time.time() - self.metrics["start_time"]
        avg_response_time = sum(self.metrics["response_times"]) / len(self.metrics["response_times"]) if self.metrics["response_times"] else 0
        
        result = {
            "uptime_seconds": uptime,
            "total_requests": self.metrics["requests"],
            "total_errors": self.metrics["errors"],
            "error_rate": (self.metrics["errors"] / self.metrics["requests"]) if self.metrics["requests"] > 0 else 0,
            "avg_response_time_ms": avg_response_time,
            "endpoints": {}
        }
        
        # Add endpoint statistics
        for endpoint, data in self.metrics["endpoints"].items():
            avg_endpoint_time = sum(data["response_times"]) / len(data["response_times"]) if data["response_times"] else 0
            result["endpoints"][endpoint] = {
                "requests": data["requests"],
                "errors": data["errors"],
                "error_rate": (data["errors"] / data["requests"]) if data["requests"] > 0 else 0,
                "avg_response_time_ms": avg_endpoint_time
            }
        
        return result
    
    def reset_metrics(self):
        """Reset all metrics."""
        self._initialize()


# Create metrics instance
metrics = Metrics()


def measure_time(func: Callable) -> Callable:
    """Decorator to measure function execution time.
    
    Args:
        func: The function to measure
        
    Returns:
        Wrapped function that logs execution time
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # Convert to ms
            app_logger.debug(f"Function {func.__name__} took {execution_time:.2f}ms to execute")
    return wrapper


def log_request(endpoint: str, log_inputs: bool = False) -> Callable:
    """Decorator to log API requests.
    
    Args:
        endpoint: Name of the endpoint
        log_inputs: Whether to log the input parameters
        
    Returns:
        Wrapped function that logs request details
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            
            # Log request inputs if enabled
            if log_inputs:
                # Safely convert args/kwargs to string representation
                args_str = str(args) if args else ""
                kwargs_str = json.dumps({k: str(v) for k, v in kwargs.items()}) if kwargs else ""
                app_logger.info(f"Request to {endpoint}: args={args_str}, kwargs={kwargs_str}")
            else:
                app_logger.info(f"Request to {endpoint}")
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                app_logger.exception(f"Error in {endpoint}: {str(e)}")
                raise
            finally:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to ms
                
                # Track in metrics
                metrics.track_request(endpoint, response_time, status_code)
                
                app_logger.info(f"Response from {endpoint}: status={status_code}, time={response_time:.2f}ms")
        
        return wrapper
    return decorator 
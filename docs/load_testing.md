# Load Testing Guide for Sequential Questioning MCP Server

This guide provides comprehensive instructions for conducting load testing on the Sequential Questioning MCP Server to ensure it meets performance requirements under various load conditions.

## Prerequisites

Before starting load testing, ensure you have:

- Python 3.8 or later installed
- Locust load testing framework (`pip install locust`)
- Additional required libraries: `requests`, `python-dotenv`
- Access to the Sequential Questioning MCP Server instance
- API key for authentication (if required)
- Sufficient permissions to run tests against the target environment

## Key Metrics to Monitor

When load testing the Sequential Questioning MCP Server, focus on these key metrics:

| Metric | Description | Target Threshold |
|--------|-------------|------------------|
| Response Time | Time to process and respond to requests | < 500ms (p95) |
| Throughput | Requests processed per second | > 100 RPS |
| Error Rate | Percentage of failed requests | < 1% |
| CPU Usage | Server CPU utilization | < 70% |
| Memory Usage | Server memory consumption | < 70% |
| Concurrent Users | Number of simultaneous users | Varies by requirements |

## Basic Load Test Example

Here's a basic Locust script (`locustfile.py`) for testing the Sequential Questioning MCP Server:

```python
import json
import random
import uuid
from locust import HttpUser, task, between

class SequentialQuestioningUser(HttpUser):
    wait_time = between(3, 7)  # Simulate realistic user thinking time
    
    def on_start(self):
        # Initialize user data
        self.user_id = str(uuid.uuid4())
        self.conversation_id = None
        self.session_id = None
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.environment.parsed_options.api_key}"
        }
    
    @task(1)
    def health_check(self):
        # Simple health check
        self.client.get("/health", name="Health Check")
    
    @task(3)
    def generate_initial_question(self):
        # Generate the first question in a new conversation
        payload = {
            "user_id": self.user_id,
            "context": "Learning about Python programming",
            "previous_messages": []
        }
        
        with self.client.post(
            "/mcp/v1/sequential-questioning",
            json=payload,
            headers=self.headers,
            name="Initial Question Generation",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Save IDs for follow-up requests
                self.conversation_id = data["conversation_id"]
                self.session_id = data["session_id"]
                response.success()
            else:
                response.failure(f"Failed to generate initial question: {response.text}")
    
    @task(5)
    def generate_follow_up_question(self):
        # Only attempt follow-up if we have a conversation
        if not self.conversation_id:
            self.generate_initial_question()
            return
        
        # Generate a follow-up question
        payload = {
            "user_id": self.user_id,
            "context": "Learning about Python programming",
            "previous_messages": [
                {"role": "assistant", "content": "What aspects of Python are you interested in learning?"},
                {"role": "user", "content": "I'm interested in Python's data analysis capabilities."}
            ],
            "conversation_id": self.conversation_id,
            "session_id": self.session_id
        }
        
        with self.client.post(
            "/mcp/v1/sequential-questioning",
            json=payload,
            headers=self.headers,
            name="Follow-up Question Generation",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to generate follow-up question: {response.text}")
```

### Running the Test

To run the load test:

1. Save the script as `locustfile.py`
2. Run Locust:
   ```bash
   locust --host=https://your-server-url.com --api-key=your_api_key_here
   ```
3. Open your browser at `http://localhost:8089` to access the Locust web interface
4. Configure the number of users and spawn rate, then start the test

## Interpreting Results

After running your test, analyze these key sections in the Locust UI:

1. **Request Statistics**: Shows response times, request counts, and failure rates
2. **Charts**: Visual representation of response times and requests per second
3. **Failures**: Details of any failed requests, including error messages
4. **Download Data**: Export results as CSV for further analysis

## Load Test Scenarios

Different scenarios help identify various performance characteristics:

### Ramp-up Test
Gradually increase the user load to identify the breaking point.

```bash
locust --host=https://your-server-url.com --headless -u 300 -r 10 -t 10m --api-key=your_api_key_here
```

### Sustained Load Test
Maintain a steady load to evaluate system stability over time.

```bash
locust --host=https://your-server-url.com --headless -u 100 -r 20 -t 30m --api-key=your_api_key_here
```

### Spike Test
Rapidly increase user load to simulate traffic spikes.

```bash
locust --host=https://your-server-url.com --headless -u 500 -r 100 -t 5m --api-key=your_api_key_here
```

## Advanced Monitoring

You can add custom metrics using Locust's event hooks. For example:

```python
from locust import events

@events.request_failure.add_listener
def on_request_failure(request_type, name, response_time, exception, **kwargs):
    print(f"Request {name} failed with exception: {exception}")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("A new test is starting")
```

## Performance Optimization Tips

If your load tests identify performance issues, consider these optimization strategies:

1. **Caching**: Implement caching for frequently accessed data
2. **Database Indexing**: Ensure proper indexes for frequently queried fields
3. **Connection Pooling**: Use database connection pooling
4. **Horizontal Scaling**: Add more server instances behind a load balancer
5. **Rate Limiting**: Implement rate limiting to prevent abuse
6. **Asynchronous Processing**: Move time-consuming tasks to background workers

## Recommended Testing Schedule

| Stage | Frequency | Load Level | Duration |
|-------|-----------|------------|----------|
| Development | Weekly | 30% of expected load | 10 minutes |
| Staging | Bi-weekly | 60% of expected load | 30 minutes |
| Pre-Production | Monthly | 100% of expected load | 1 hour |
| Post-Deployment | After each major release | 120% of expected load | 2 hours |

## Troubleshooting Common Issues

| Issue | Potential Cause | Solution |
|-------|-----------------|----------|
| High Response Times | Database bottlenecks | Optimize queries, add indexes |
| Memory Leaks | Resource not being released | Check for proper cleanup in code |
| Database Bottlenecks | Inefficient queries | Use query profiling, optimize SQL |
| Network Timeouts | Connection pool exhaustion | Increase connection pool size |

## CI/CD Integration

Integrate load testing into your CI/CD pipeline using this GitHub Actions example:

```yaml
name: Load Testing

on:
  workflow_dispatch:
  schedule:
    - cron: '0 0 * * 1'  # Run every Monday at midnight

jobs:
  load_test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install locust
          
      - name: Run load test
        run: |
          locust -f locustfile.py --headless -u 100 -r 10 -t 5m --host https://your-staging-server.com --api-key ${{ secrets.API_KEY }}
          
      - name: Save test results
        uses: actions/upload-artifact@v2
        with:
          name: load-test-results
          path: locust_stats.csv
```

## Conclusion

Regular load testing is essential to ensure the Sequential Questioning MCP Server can handle expected traffic and maintain performance. Follow this guide to establish a testing regimen that provides confidence in your system's capabilities.

For further assistance, contact the development team at [support@example.com](mailto:support@example.com). 
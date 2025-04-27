# API Usage Examples

This document provides examples of how to use the Sequential Questioning MCP Server API for different scenarios.

## Authentication

All API requests require an API key to be provided in the header:

```
Authorization: Bearer your_api_key_here
```

## 1. Generating an Initial Question

To generate an initial question for a user, make a POST request to the sequential questioning endpoint without providing any previous messages.

### Request

```bash
curl -X POST \
  http://localhost:8000/mcp/sequential-questioning \
  -H 'Authorization: Bearer your_api_key_here' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "user123",
    "context": "Customer is looking for information about travel insurance for a family vacation to Europe."
  }'
```

### Response

```json
{
  "question": "What are the specific countries in Europe that you plan to visit during your family vacation?",
  "conversation_id": "conv_01H2X3Y4Z5W6V7U8T9",
  "session_id": "sess_01H2X3Y4Z5W6V7U8T9",
  "metadata": {
    "question_type": "initial",
    "intent": "destination_details",
    "priority": "high"
  }
}
```

## 2. Generating a Follow-up Question

To generate a follow-up question, include the previous messages in the request.

### Request

```bash
curl -X POST \
  http://localhost:8000/mcp/sequential-questioning \
  -H 'Authorization: Bearer your_api_key_here' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "user123",
    "context": "Customer is looking for information about travel insurance for a family vacation to Europe.",
    "previous_messages": [
      {
        "role": "assistant",
        "content": "What are the specific countries in Europe that you plan to visit during your family vacation?"
      },
      {
        "role": "user",
        "content": "We plan to visit France, Italy, and Spain over a period of 3 weeks."
      }
    ],
    "session_id": "sess_01H2X3Y4Z5W6V7U8T9",
    "conversation_id": "conv_01H2X3Y4Z5W6V7U8T9"
  }'
```

### Response

```json
{
  "question": "How many family members will be traveling and what are their ages?",
  "conversation_id": "conv_01H2X3Y4Z5W6V7U8T9",
  "session_id": "sess_01H2X3Y4Z5W6V7U8T9",
  "metadata": {
    "question_type": "follow_up",
    "intent": "traveler_details",
    "priority": "high"
  }
}
```

## 3. Continuing a Conversation

For a longer conversation, continue to include all previous exchanges.

### Request

```bash
curl -X POST \
  http://localhost:8000/mcp/sequential-questioning \
  -H 'Authorization: Bearer your_api_key_here' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "user123",
    "context": "Customer is looking for information about travel insurance for a family vacation to Europe.",
    "previous_messages": [
      {
        "role": "assistant",
        "content": "What are the specific countries in Europe that you plan to visit during your family vacation?"
      },
      {
        "role": "user",
        "content": "We plan to visit France, Italy, and Spain over a period of 3 weeks."
      },
      {
        "role": "assistant",
        "content": "How many family members will be traveling and what are their ages?"
      },
      {
        "role": "user",
        "content": "We are 2 adults (35 and 38) and 2 children (7 and 10)."
      }
    ],
    "session_id": "sess_01H2X3Y4Z5W6V7U8T9",
    "conversation_id": "conv_01H2X3Y4Z5W6V7U8T9"
  }'
```

### Response

```json
{
  "question": "Do any of the travelers have pre-existing medical conditions that would require special coverage?",
  "conversation_id": "conv_01H2X3Y4Z5W6V7U8T9",
  "session_id": "sess_01H2X3Y4Z5W6V7U8T9",
  "metadata": {
    "question_type": "follow_up",
    "intent": "medical_details",
    "priority": "high"
  }
}
```

## 4. Starting a New Conversation with the Same User

To start a new conversation with an existing user, omit the conversation_id and session_id.

### Request

```bash
curl -X POST \
  http://localhost:8000/mcp/sequential-questioning \
  -H 'Authorization: Bearer your_api_key_here' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "user123",
    "context": "Customer is inquiring about adding rental car coverage to an existing travel insurance policy."
  }'
```

### Response

```json
{
  "question": "Can you provide your existing travel insurance policy number?",
  "conversation_id": "conv_02J3K4L5M6N7P8Q9R0",
  "session_id": "sess_02J3K4L5M6N7P8Q9R0",
  "metadata": {
    "question_type": "initial",
    "intent": "policy_identification",
    "priority": "high"
  }
}
```

## 5. Monitoring API Usage

To retrieve metrics about the API usage, use the monitoring endpoint.

### Request

```bash
curl -X GET \
  http://localhost:8000/mcp-internal/monitoring/metrics \
  -H 'Authorization: Bearer your_api_key_here'
```

### Response

```json
{
  "requests": {
    "total": 42,
    "success": 40,
    "error": 2
  },
  "endpoints": {
    "/mcp/sequential-questioning": {
      "count": 38,
      "avg_response_time": 1.25
    },
    "/health": {
      "count": 4,
      "avg_response_time": 0.01
    }
  },
  "errors": {
    "ValidationError": 1,
    "ServiceUnavailable": 1
  },
  "response_times": {
    "avg": 1.15,
    "min": 0.01,
    "max": 3.45,
    "p95": 2.8,
    "p99": 3.2
  }
}
```

### Resetting Metrics

To reset the metrics counter:

```bash
curl -X POST \
  http://localhost:8000/mcp-internal/monitoring/reset \
  -H 'Authorization: Bearer your_api_key_here'
```

## 6. Health Check

To check if the API is running:

```bash
curl -X GET http://localhost:8000/health
```

Response:

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## Integration Examples

### Python Example

```python
import requests
import json

API_URL = "http://localhost:8000"
API_KEY = "your_api_key_here"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Generate initial question
def get_initial_question(user_id, context):
    payload = {
        "user_id": user_id,
        "context": context
    }
    
    response = requests.post(
        f"{API_URL}/mcp/sequential-questioning",
        headers=headers,
        data=json.dumps(payload)
    )
    
    return response.json()

# Generate follow-up question
def get_follow_up_question(user_id, context, previous_messages, session_id, conversation_id):
    payload = {
        "user_id": user_id,
        "context": context,
        "previous_messages": previous_messages,
        "session_id": session_id,
        "conversation_id": conversation_id
    }
    
    response = requests.post(
        f"{API_URL}/mcp/sequential-questioning",
        headers=headers,
        data=json.dumps(payload)
    )
    
    return response.json()

# Example usage
user_id = "user123"
context = "Customer is inquiring about home insurance options."

# Get initial question
initial_response = get_initial_question(user_id, context)
print(f"Initial question: {initial_response['question']}")

# Store the conversation and session IDs
conversation_id = initial_response["conversation_id"]
session_id = initial_response["session_id"]

# Simulate user response
previous_messages = [
    {
        "role": "assistant",
        "content": initial_response["question"]
    },
    {
        "role": "user",
        "content": "I have a 3-bedroom house in Seattle, built in 2005."
    }
]

# Get follow-up question
follow_up_response = get_follow_up_question(
    user_id,
    context,
    previous_messages,
    session_id,
    conversation_id
)

print(f"Follow-up question: {follow_up_response['question']}")
```

### JavaScript Example

```javascript
const axios = require('axios');

const API_URL = 'http://localhost:8000';
const API_KEY = 'your_api_key_here';

const headers = {
  'Authorization': `Bearer ${API_KEY}`,
  'Content-Type': 'application/json'
};

// Generate initial question
async function getInitialQuestion(userId, context) {
  try {
    const response = await axios.post(
      `${API_URL}/mcp/sequential-questioning`,
      {
        user_id: userId,
        context: context
      },
      { headers }
    );
    
    return response.data;
  } catch (error) {
    console.error('Error generating initial question:', error.response?.data || error.message);
    throw error;
  }
}

// Generate follow-up question
async function getFollowUpQuestion(userId, context, previousMessages, sessionId, conversationId) {
  try {
    const response = await axios.post(
      `${API_URL}/mcp/sequential-questioning`,
      {
        user_id: userId,
        context: context,
        previous_messages: previousMessages,
        session_id: sessionId,
        conversation_id: conversationId
      },
      { headers }
    );
    
    return response.data;
  } catch (error) {
    console.error('Error generating follow-up question:', error.response?.data || error.message);
    throw error;
  }
}

// Example usage
async function exampleUsage() {
  const userId = 'user123';
  const context = 'Customer is inquiring about auto insurance after purchasing a new vehicle.';
  
  try {
    // Get initial question
    const initialResponse = await getInitialQuestion(userId, context);
    console.log(`Initial question: ${initialResponse.question}`);
    
    // Store the conversation and session IDs
    const conversationId = initialResponse.conversation_id;
    const sessionId = initialResponse.session_id;
    
    // Simulate user response
    const previousMessages = [
      {
        role: 'assistant',
        content: initialResponse.question
      },
      {
        role: 'user',
        content: 'I just bought a 2023 Toyota Camry.'
      }
    ];
    
    // Get follow-up question
    const followUpResponse = await getFollowUpQuestion(
      userId,
      context,
      previousMessages,
      sessionId,
      conversationId
    );
    
    console.log(`Follow-up question: ${followUpResponse.question}`);
  } catch (error) {
    console.error('Example usage failed:', error);
  }
}

exampleUsage();
``` 
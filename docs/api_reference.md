# API Reference

This document provides a complete reference for all API endpoints in the Sequential Questioning MCP Server.

## MCP Endpoints

### Generate Sequential Question

Generates a contextually relevant question based on conversation history.

```
POST /mcp/sequential-questioning
```

#### Request Body

```json
{
  "user_id": "string",
  "context": "string",
  "previous_messages": [
    {
      "role": "string",
      "content": "string"
    }
  ]
}
```

**Parameters:**

- `user_id` (required): Unique identifier for the user
- `context` (required): Initial context for the conversation
- `previous_messages` (optional): List of previous messages in the conversation
  - `role`: Either "user" or "assistant" 
  - `content`: The content of the message

#### Response

```json
{
  "conversation_id": "string",
  "session_id": "string",
  "question": "string",
  "metadata": {
    "generation_time": "float",
    "tokens_used": "integer",
    "similar_contexts": [
      "string"
    ]
  }
}
```

**Fields:**

- `conversation_id`: Unique identifier for the conversation
- `session_id`: Unique identifier for the user session
- `question`: The generated question
- `metadata`: Additional information about the generation process
  - `generation_time`: Time taken to generate the question in seconds
  - `tokens_used`: Number of tokens used in the generation process
  - `similar_contexts`: Similar contexts found in the vector database (if any)

#### Error Responses

- **400 Bad Request**: Invalid request parameters
- **500 Internal Server Error**: Failed to generate question

## Internal Endpoints

### Health Check

```
GET /health
```

#### Response

```json
{
  "status": "ok",
  "version": "string",
  "timestamp": "string"
}
```

### Metrics

```
GET /mcp-internal/monitoring/metrics
```

#### Response

```json
{
  "requests": {
    "total": "integer",
    "by_endpoint": {
      "endpoint_path": "integer"
    }
  },
  "errors": {
    "total": "integer",
    "by_type": {
      "error_type": "integer"
    }
  },
  "response_times": {
    "avg": "float",
    "min": "float",
    "max": "float",
    "p95": "float",
    "p99": "float"
  }
}
```

### Reset Metrics

```
POST /mcp-internal/monitoring/reset
```

#### Response

```json
{
  "status": "success",
  "message": "Metrics reset successfully"
}
```

## Using the API

### Authentication

Currently, the API does not require authentication. This will be added in future versions.

### Rate Limiting

Rate limiting is not implemented in the current version.

### Example Request (cURL)

```bash
curl -X POST "http://localhost:8000/mcp/sequential-questioning" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "context": "We are discussing climate change and its effects on agriculture.",
    "previous_messages": [
      {
        "role": "user",
        "content": "How does rising temperature affect crop yields?"
      },
      {
        "role": "assistant",
        "content": "Rising temperatures can reduce crop yields through heat stress, increased water demand, and changes in pest populations."
      }
    ]
  }'
```

### Example Response

```json
{
  "conversation_id": "conv_9f8a7b6c5d",
  "session_id": "sess_1a2b3c4d5e",
  "question": "What specific crops are most vulnerable to these temperature increases, and are there any regions particularly at risk?",
  "metadata": {
    "generation_time": 1.25,
    "tokens_used": 128,
    "similar_contexts": [
      "Discussion about drought-resistant crops in warming climates"
    ]
  }
}
``` 
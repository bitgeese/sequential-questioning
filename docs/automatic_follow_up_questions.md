# Automatic Follow-Up Questions

This document explains how to use the automatic follow-up questions feature in the Sequential Questioning MCP Server.

## Overview

The Sequential Questioning MCP Server now provides three different endpoints for generating questions:

1. **Basic Question Generation** - `/mcp-internal/question`
2. **Follow-Up Question Generation** - `/mcp-internal/question/follow-up` 
3. **Automatic Multi-Round Questioning** - `/mcp-internal/question/automatic`

These endpoints allow for different levels of automation in the question generation process, from simple single-round questioning to fully automatic multi-round questioning with follow-ups.

## Endpoint Comparison

| Feature | Basic Question | Follow-Up Question | Automatic Multi-Round |
| --- | --- | --- | --- |
| Operation ID | `sequentialQuestioning` | `sequentialQuestioningFollowUp` | `sequentialQuestioningAutomatic` |
| Designed for | Initial questions | Explicit follow-up questions | Complete conversation flows |
| Requires conversation_id | No | Yes | No |
| Max question rounds | 1 | 1 | Configurable (1-3) |

## Automatic Multi-Round Questioning

The `/mcp-internal/question/automatic` endpoint is designed to streamline the questioning process by generating multiple rounds of questions in a single request. This is particularly useful for gathering comprehensive information from users without requiring multiple separate calls to the API.

### Request Format

```json
{
  "context": "Month planning for software developers",
  "user_id": "user-123",
  "previous_messages": [
    {
      "role": "user",
      "content": "I need help planning my workload for the next month with multiple ongoing projects."
    }
  ],
  "auto_handle_follow_up": true,
  "max_rounds": 2
}
```

### Parameters

- `context` (string, optional): Provides context for question generation
- `user_id` (string, optional): User identifier for tracking conversations
- `previous_messages` (array, optional): Previous messages in the conversation
- `auto_handle_follow_up` (boolean, default: true): Whether to automatically generate follow-up questions
- `max_rounds` (integer, default: 2): Maximum number of question rounds to generate (capped at 3)

### Response Format

```json
{
  "initial_questions": {
    "current_question": "...",
    "questions": [
      {
        "question_text": "...",
        "question_number": 1,
        "metadata": { ... }
      },
      ...
    ],
    "conversation_id": "...",
    "session_id": "...",
    "current_question_number": 1,
    "total_questions_in_batch": 5,
    "total_questions_estimated": 10,
    "next_batch_needed": true,
    "metadata": { ... }
  },
  "follow_up_questions": [
    {
      "current_question": "...",
      "questions": [ ... ],
      ...
    }
  ],
  "all_questions_combined": "1. First question\n2. Second question\n...",
  "conversation_id": "...",
  "session_id": "...",
  "total_questions": 8,
  "metadata": {
    "rounds_generated": 2,
    "timestamp": "2025-05-15T12:34:56.789012",
    "auto_follow_up": true
  }
}
```

### Displaying Questions to Users

The `all_questions_combined` field contains a formatted string with all questions from all rounds, numbered sequentially. This makes it easy to present all questions to the user at once.

## Example Usage with cURL

```bash
curl -X POST "http://localhost:8000/mcp-internal/question/automatic" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "Month planning for software developers",
    "user_id": "test-user",
    "previous_messages": [
      {
        "role": "user",
        "content": "I need help planning my workload for the next month with multiple ongoing projects."
      }
    ],
    "max_rounds": 2
  }'
```

## Example Usage in an LLM Tool

```python
def sequential_questioning_tool(context, user_id=None, conversation_id=None, previous_messages=None, max_rounds=2):
    """
    MCP tool for generating multi-round sequential questions.
    
    Args:
        context: The context for question generation
        user_id: Optional user identifier
        conversation_id: Optional conversation identifier for follow-up questions
        previous_messages: List of previous messages in the conversation
        max_rounds: Maximum number of question rounds to generate
        
    Returns:
        A formatted string with numbered questions
    """
    url = "http://localhost:8000/mcp-internal/question/automatic"
    
    payload = {
        "context": context,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "previous_messages": previous_messages,
        "max_rounds": max_rounds
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    
    data = response.json()
    return data["all_questions_combined"]
```

## Best Practices

1. **Balance Depth vs. Length** - While more rounds provide more comprehensive questioning, they can also lead to lengthy exchanges. Consider your user experience when setting `max_rounds`.

2. **Provide Rich Context** - The quality of generated questions improves with better context. Include relevant details about the topic and user needs.

3. **Include Previous Answers** - When using the automatic questioning feature, including previous user answers in `previous_messages` helps generate more relevant follow-up questions.

4. **Handle Long Responses** - When presenting multiple questions to users, ensure your UI can handle potentially lengthy responses.

5. **Conversation Continuity** - Store the `conversation_id` and `session_id` from responses to maintain conversation context for future interactions. 
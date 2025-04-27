# Sequential Questioning MCP Server Architecture

## System Overview

The Sequential Questioning MCP Server is designed to provide contextually relevant questions based on conversation history. The system uses a combination of LLMs (Large Language Models) and vector embeddings to generate intelligent follow-up questions that maintain context across a conversation.

## Core Components

### 1. API Layer

- **FastAPI Application**: The main entry point for the application, handling HTTP requests and responses.
- **MCP Endpoints**: Custom endpoints that follow the MCP (Model-Controlled Processing) pattern for structured question generation.
- **Internal Endpoints**: Endpoints for monitoring and administration.

### 2. Service Layer

- **Question Generation Service**: Core business logic for generating initial and follow-up questions.
- **Vector Database Service**: Integration with Qdrant for storing and retrieving vector embeddings.

### 3. Repository Layer

- **User Session Repository**: Manages user session data and persistence.
- **Conversation Repository**: Handles conversation storage and retrieval.
- **Message Repository**: Manages individual message data.

### 4. Model Layer

- **Domain Models**: SQLAlchemy models representing core business entities.
- **Data Transfer Objects**: Pydantic schemas for request/response validation.

### 5. Core Infrastructure

- **Database**: SQLite for development, with SQLAlchemy as the ORM.
- **Vector Database**: Qdrant for storing and searching vector embeddings.
- **Monitoring**: Custom metrics collection and reporting.

## Data Flow

1. **Question Generation Flow**:
   - Client sends a request to the MCP endpoint
   - Request is validated and processed
   - Question generation service is invoked
   - For follow-up questions, previous context is retrieved and enhanced with vector database
   - LLM generates a question based on context
   - Response is formatted and returned to the client

2. **Data Persistence Flow**:
   - User sessions, conversations, and messages are stored in SQLite
   - Vector embeddings are stored in Qdrant
   - Repositories handle the data access logic

## Component Interaction Diagram

```
Client → FastAPI → MCP Endpoint → Question Generation Service → LLM
                                                              ↑
                                                              ↓
  SQLite ← Repositories ← Services → Vector DB Service → Qdrant
```

## Monitoring and Observability

The system includes a comprehensive monitoring solution:

- **Request tracking**: Count of requests per endpoint
- **Error tracking**: Error rates and types
- **Performance metrics**: Response times, percentiles
- **API metrics endpoint**: Exposes collected metrics via REST API

## Deployment Architecture

The application is containerized using Docker:

- **Application Container**: Runs the FastAPI application
- **Vector Database Container**: Runs Qdrant
- **Docker Compose**: Orchestrates the containers and networking

## Security Considerations

- **Input Validation**: All input is validated using Pydantic schemas
- **Error Handling**: Comprehensive error handling prevents information leakage
- **Dependency Injection**: Uses FastAPI's dependency injection for clean, testable code

## Extensibility Points

The architecture is designed for extensibility:

- **Custom Question Generators**: Additional question generation strategies can be implemented
- **Alternative Vector Databases**: The vector database service can be adapted for different providers
- **Pluggable LLMs**: Different language models can be used for question generation 
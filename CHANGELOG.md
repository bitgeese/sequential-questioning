# Changelog

All notable changes to the Sequential Questioning MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2023-06-20

### Added
- Initial production release
- Core question generation engine
- MCP protocol support with fastapi-mcp integration
- Conversation management API endpoints
- User session tracking and history
- Vector search using Qdrant
- PostgreSQL database integration with SQLAlchemy
- Metrics collection and monitoring with Prometheus
- Comprehensive documentation
- Kubernetes deployment configurations
- CI/CD pipeline with GitHub Actions
- Performance tests and benchmarks

### Changed
- Optimized vector search for better question relevance
- Improved error handling and reporting
- Enhanced logging with structured JSON format
- Refactored codebase for better maintainability
- Updated database configuration to properly use asyncpg driver for PostgreSQL connections
- Improved Qdrant vector database connection with retry mechanism and graceful degradation
- Updated LangChain imports to use the community package for compatibility

### Fixed
- Database connection pooling issues
- Memory leaks in long-running processes
- Race conditions in concurrent conversations
- Error handling in API endpoints
- Fixed asyncio SQLAlchemy engine configuration to use the correct async driver
- Fixed Qdrant connection issues with better error handling and retries
- Fixed deprecated LangChain imports

## [0.9.0] - 2023-05-15

### Added
- Beta release with core functionality
- Initial implementation of question generation
- Basic conversation tracking
- Simple API endpoints
- Docker containerization
- Initial test suite

### Fixed
- Various bugs in the question generation algorithm
- Error handling in database access
- Performance issues with large conversations

## [0.5.0] - 2023-04-01

### Added
- Alpha release for internal testing
- Proof of concept for question generation
- Basic API structure
- Initial database models
- Docker development environment

## [0.1.0] - 2023-03-01

### Added
- Project initialization
- Initial architecture design
- Repository setup
- Development environment configuration 
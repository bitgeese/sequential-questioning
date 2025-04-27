# Contributing to Sequential Questioning MCP Server

Thank you for your interest in contributing to Sequential Questioning MCP Server! This document provides guidelines and instructions for contributors.

## Code of Conduct

We expect all contributors to adhere to professional standards when interacting with the project. Be respectful, inclusive, and constructive in your communications.

## Getting Started

1. **Fork the Repository**
   - Create a fork of the repository on GitHub
   - Clone your fork locally

2. **Set Up Development Environment**
   - Follow the installation instructions in the README.md
   - Create a virtual environment
   - Install development dependencies:
     ```bash
     pip install -e ".[dev]"
     ```

3. **Create a Feature Branch**
   - Use descriptive branch names with the format: `feature/your-feature-name` or `fix/issue-description`
   - Keep branches focused on a single feature or fix

## Development Workflow

### Code Style

This project follows PEP 8 style guidelines with some modifications:

- Line length: 88 characters (configured in pyproject.toml)
- Use type hints for all function parameters and return values
- Format code with Black before submitting

Run linting and formatting:

```bash
# Format code
black app tests

# Sort imports
isort app tests

# Run linting
ruff app tests

# Type checking
mypy app tests
```

### Writing Tests

All new features should include appropriate tests:

- Unit tests for models, repositories, and services
- Integration tests for complex interactions
- API tests for new endpoints

Run tests with:

```bash
pytest
```

To run tests with coverage:

```bash
pytest --cov=app tests/
```

### Documentation

Always update documentation when adding or changing features:

- Add docstrings to all functions, classes, and modules
- Update API reference for new or modified endpoints
- Add usage examples for significant features
- Update architecture documentation for design changes

## Pull Request Process

1. **Create a Pull Request**
   - Ensure all tests pass before submitting
   - Reference any related issues in the PR description
   - Provide a clear description of the changes and their purpose

2. **Code Review**
   - Address all feedback from reviewers
   - Make requested changes in the same branch and push updates

3. **Approval and Merge**
   - PRs require at least one approval before merging
   - Maintainers will handle the final merge

## Project Structure

```
sequential-questioning/
├── app/
│   ├── api/          # API endpoints and dependencies
│   ├── core/         # Core functionality (config, monitoring)
│   ├── mcp/          # MCP interface implementation
│   ├── models/       # Data models and database schemas
│   ├── repositories/ # Data access layer
│   ├── services/     # Business logic
│   └── main.py       # Application entry point
├── tests/
│   ├── api/          # API endpoint tests
│   ├── integration/  # Integration tests
│   ├── mcp/          # MCP interface tests
│   ├── models/       # Model tests
│   └── services/     # Service tests
├── docs/             # Documentation
└── ...               # Config files
```

## Working with Dependencies

When adding new dependencies:

1. Add them to the appropriate section in pyproject.toml
2. Document the purpose of the dependency in a comment or PR description
3. Regenerate any lock files if necessary

## Database Changes

When making database schema changes:

1. Create a new Alembic migration:
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   ```
2. Review the generated migration file
3. Test the migration both up and down
4. Document the schema changes in the PR description

## Vector Database Changes

When modifying vector database structure:

1. Document the changes in architecture.md
2. Update the relevant services
3. Provide migration steps for existing data if applicable

## Versioning

This project follows Semantic Versioning (SemVer):

- MAJOR version for incompatible API changes
- MINOR version for new functionality in a backward-compatible manner
- PATCH version for backward-compatible bug fixes

## Questions and Support

If you have questions or need help:

1. Check existing documentation
2. Open an issue with the "question" label
3. Contact the maintainers

Thank you for contributing to the Sequential Questioning MCP Server! 
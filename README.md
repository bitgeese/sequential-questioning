# Sequential Questioning MCP Server

A specialized server that enables LLMs (Large Language Models) to gather specific information through sequential questioning. This project implements the MCP (Model Control Protocol) standard for seamless integration with LLM clients.

## Project Status

🎉 **Version 1.0.0 Released** 🎉

The Sequential Questioning MCP Server is now complete and ready for production deployment. All planned features have been implemented, tested, and documented.

## Features

- **Sequential Questioning Engine**: Generates contextually appropriate follow-up questions based on previous responses
- **MCP Protocol Support**: Full implementation of the MCP specification for integration with LLMs
- **Robust API**: RESTful API with comprehensive validation and error handling
- **Vector Database Integration**: Efficient storage and retrieval of question patterns
- **Comprehensive Monitoring**: Performance metrics and observability with Prometheus and Grafana
- **Production-Ready Deployment**: Kubernetes deployment configuration with multi-environment support
- **High Availability**: Horizontal Pod Autoscaler and Pod Disruption Budget for production reliability
- **Security**: Network policies to restrict traffic and secure the application

## Documentation

- [API Reference](docs/api_reference.md)
- [Architecture](docs/architecture.md)
- [Usage Examples](docs/usage_examples.md)
- [Deployment Guide](docs/deployment.md)
- [Operational Runbook](docs/operational_runbook.md)
- [Load Testing](docs/load_testing.md)
- [Deployment Verification](docs/deployment_verification.md)
- [Final Deployment Plan](docs/final_deployment_plan.md)
- [Release Notes](docs/project_release_notes.md)

## Getting Started

### Prerequisites

- Python 3.10+
- Docker and Docker Compose (for local development)
- Kubernetes cluster (for production deployment)
- PostgreSQL 15.4+
- Access to a Qdrant instance

### Quick Start

The easiest way to get started is to use our initialization script:

```bash
./scripts/initialize_app.sh
```

This script will:
1. Check if Docker is running
2. Start all necessary containers with Docker Compose
3. Run database migrations automatically
4. Provide information on how to access the application

The application will be available at http://localhost:8001

### Local Development

1. Clone the repository
   ```bash
   git clone https://github.com/your-organization/sequential-questioning.git
   cd sequential-questioning
   ```

2. Install dependencies
   ```bash
   pip install -e ".[dev]"
   ```

3. Set up environment variables
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

4. Run the development server
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Deployment

```bash
docker-compose up -d
```

### Database Setup

If you're starting the application manually, don't forget to run the database migrations:

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/postgres"
bash scripts/run_migrations.sh
```

### Kubernetes Deployment

1. Development Environment
   ```bash
   kubectl apply -k k8s/overlays/dev
   ```

2. Staging Environment
   ```bash
   kubectl apply -k k8s/overlays/staging
   ```

3. Production Environment
   ```bash
   kubectl apply -k k8s/overlays/prod
   ```

See the [Final Deployment Plan](docs/final_deployment_plan.md) and [Operational Runbook](docs/operational_runbook.md) for detailed instructions.

## Monitoring

Access Prometheus and Grafana dashboards for monitoring:

```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
kubectl port-forward -n monitoring svc/grafana 3000:3000
```

## CI/CD Pipeline

Automated CI/CD pipeline with GitHub Actions:
- Continuous Integration: Linting, type checking, and testing
- Continuous Deployment: Automated deployments to dev, staging, and production
- Deployment Verification: Automated checks post-deployment

## Testing

Run the test suite:

```bash
pytest
```

Run performance tests:

```bash
python -m tests.performance.test_sequential_questioning_load
```

## Troubleshooting

### Database Tables Not Created

If the application is running but the database tables don't exist:

1. Make sure the database container is running
2. Run the database migrations manually:
   ```bash
   export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/postgres"
   bash scripts/run_migrations.sh
   ```

### Pydantic Version Compatibility

If you encounter the error `pydantic.errors.PydanticImportError: BaseSettings has been moved to the pydantic-settings package`, ensure that:

1. The `pydantic-settings` package is included in your dependencies
2. You're importing `BaseSettings` from `pydantic_settings` instead of directly from `pydantic`

This project uses Pydantic v2.x which moved `BaseSettings` to a separate package.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT License](LICENSE)

## Contact

For support or inquiries, contact support@example.com 
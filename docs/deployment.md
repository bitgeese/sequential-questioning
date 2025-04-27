# Deployment Guide for Sequential Questioning MCP Server

This guide outlines the steps to deploy the Sequential Questioning MCP Server in various environments.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.10 or higher (if not using Docker)
- Access to a PostgreSQL database
- Access to a Qdrant vector database instance (or use the Docker Compose configuration)
- API key for the LLM service (OpenAI or equivalent)

## Environment Variables

Create a `.env` file with the following variables:

```
# Database Configuration
DATABASE_URL=postgresql://user:password@db:5432/sequential_questioning
DATABASE_USER=user
DATABASE_PASSWORD=password
DATABASE_NAME=sequential_questioning
DATABASE_HOST=db
DATABASE_PORT=5432

# Application Configuration
API_KEY=your_api_key_here
DEBUG=false
ENVIRONMENT=production
LOG_LEVEL=info

# Vector Database Configuration
VECTOR_DB_URL=http://qdrant:6333
VECTOR_COLLECTION_NAME=questions

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key_here
MODEL_NAME=gpt-4-turbo
```

Adjust these values according to your deployment environment.

## Deployment Options

### Option 1: Docker Compose (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/sequential-questioning.git
   cd sequential-questioning
   ```

2. Create the `.env` file as described above.

3. Build and run the services:
   ```bash
   docker-compose up -d
   ```

4. The API will be available at `http://localhost:8000`.

### Option 2: Manual Deployment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/sequential-questioning.git
   cd sequential-questioning
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

4. Create the `.env` file as described above, adjusting the database URL to point to your PostgreSQL instance.

5. Run the application:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### Option 3: Kubernetes Deployment

1. Create Kubernetes configuration files:

   **deployment.yaml**:
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: sequential-questioning
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: sequential-questioning
     template:
       metadata:
         labels:
           app: sequential-questioning
       spec:
         containers:
         - name: sequential-questioning
           image: yourdockerregistry/sequential-questioning:latest
           ports:
           - containerPort: 8000
           envFrom:
           - secretRef:
               name: sequential-questioning-secrets
           - configMapRef:
               name: sequential-questioning-config
   ```

   **service.yaml**:
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: sequential-questioning
   spec:
     selector:
       app: sequential-questioning
     ports:
     - port: 80
       targetPort: 8000
     type: ClusterIP
   ```

2. Create Kubernetes secrets and config maps for environment variables.

3. Apply the configuration:
   ```bash
   kubectl apply -f deployment.yaml
   kubectl apply -f service.yaml
   ```

## Health Check

Once deployed, verify the application is running correctly by accessing the health check endpoint:

```
GET /health
```

Expected response:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## Monitoring

Monitor the application using the internal monitoring endpoints:

```
GET /mcp-internal/monitoring/metrics
```

This endpoint requires the API key for authentication.

## Database Migrations

The application handles database migrations automatically on startup. However, if you need to run migrations manually:

```bash
alembic upgrade head
```

## Scaling Considerations

- The application is stateless and can be horizontally scaled by increasing the number of replicas.
- For high-traffic environments, consider implementing a load balancer.
- Monitor and adjust the database connection pool size based on load.
- Consider using a managed vector database service for production deployments.

## Backup and Recovery

- Regularly backup the PostgreSQL database.
- Backup the vector database collections.
- Store environment variables and configuration securely.

## Security Considerations

- Use HTTPS in production.
- Rotate API keys regularly.
- Implement rate limiting for API endpoints.
- Consider using a managed identity service for authentication in production. 
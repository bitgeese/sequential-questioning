#!/bin/bash
set -e

echo "Initializing Sequential Questioning MCP Server..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running or not installed. Please start Docker and try again."
  exit 1
fi

# Set environment variables for local development
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/postgres"

# Start the Docker containers
echo "Starting Docker containers..."
docker-compose up -d

# Wait for the database to be ready
echo "Waiting for database to be ready..."
sleep 10

# Run database migrations
echo "Running database migrations..."
bash scripts/run_migrations.sh

echo "Initialization completed successfully!"
echo "The application is now running at: http://localhost:8001"
echo ""
echo "Use the following command to view logs:"
echo "  docker-compose logs -f app"
echo ""
echo "To stop the application:"
echo "  docker-compose down" 
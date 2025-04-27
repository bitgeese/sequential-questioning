#!/bin/bash
set -e

echo "Running database migrations..."

# If the DATABASE_URL environment variable is not set, use a default value
if [ -z "$DATABASE_URL" ]; then
  echo "DATABASE_URL is not set. Using default local database."
  export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/sequential_questioning"
fi

# Execute the migrations
cd "$(dirname "$0")/.." # Navigate to project root
alembic upgrade head

echo "Migrations completed successfully!" 
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies including those needed for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    postgresql-client \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY pyproject.toml README.md alembic.ini ./
COPY app ./app
COPY scripts ./scripts

# Install Python dependencies
RUN pip install --no-cache-dir .
RUN pip install --no-cache-dir asyncpg psycopg2-binary
RUN pip install --no-cache-dir langchain langchain_core langchain_openai

# Verify that pydantic-settings is installed
RUN pip show pydantic-settings

# Create non-root user
RUN useradd -m appuser
USER appuser

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 